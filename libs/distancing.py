import cv2 as cv
import numpy as np
import os
import time
from libs.classifiers.classifier import Classifier
from libs.trackers.tracker import Tracker
from libs.loggers.logger import Logger
from tools.objects_post_process import extract_violating_objects
from libs.detectors.detector import Detector
from libs.source_post_processors.social_distance import SocialDistancePostProcessor
from libs.source_post_processors.objects_filtering import ObjectsFilteringPostProcessor
from libs.source_post_processors.anonymizer import AnonymizerPostProcesor
import logging


logger = logging.getLogger(__name__)


class Distancing:

    def __init__(self, config, source, live_feed_enabled=True):
        self.config = config
        self.live_feed_enabled = live_feed_enabled
        self.log_time_interval = float(self.config.get_section_dict("Logger")["TimeInterval"])  # Seconds

        self.classifier = None

        self.running_video = False
        self.tracker = Tracker(self.config)
        self.camera_id = self.config.get_section_dict(source)['Id']
        self.image_size = [int(i) for i in self.config.get_section_dict('Detector')['ImageSize'].split(',')]

        self.dist_threshold = self.config.get_section_dict("PostProcessor")["DistThreshold"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])
        self.birds_eye_resolution = (200, 300)
        self.track_hist = dict()
        if "Classifier" in self.config.get_sections():
            self.classifier = Classifier(self.config)

        self.distance = SocialDistancePostProcessor(self.config, source, 'SourcePostProcessor_1')
        self.objects_filtering = ObjectsFilteringPostProcessor(self.config, source, 'SourcePostProcessor_0')
        self.anonymizer = AnonymizerPostProcesor(self.config, source, 'SourcePostProcessor_2')

        self.video_logger = None
        if self.live_feed_enabled:
            self.video_logger = Logger(self.config, source, "SourceLogger_0")
        self.s3_logger = Logger(self.config, source, "SourceLogger_1")
        self.file_system_logger = Logger(self.config, source, "SourceLogger_2")
        self.web_hook_logger = Logger(self.config, source, "SourceLogger_3")

    def __process(self, cv_image):
        """
        return object_list list of  dict for each obj,
        obj["bbox"] is normalized coordinations for [x0, y0, x1, y1] of box
        """

        # Resize input image to resolution
        cv_image = cv.resize(cv_image, self.resolution)
        tmp_objects_list, detection_scores, class_ids, detection_bboxes, classifier_objects = self.detector.inference(cv_image)
        # Execute classifier and tracker
        if self.classifier:
            classifier_results, classifier_scores = self.classifier.inference(classifier_objects)
        tracks = self.tracker.update(detection_bboxes, class_ids, detection_scores)
        self.update_history(tracks)
        tracked_objects_list = []
        idx = 0
        for obj in tmp_objects_list:
            self.tracker.object_post_process(obj, tracks)
            if self.classifier is not None:
                if obj.get("face") is not None:
                    self.classifier.object_post_process(obj, classifier_results[idx], classifier_scores[idx])
                    idx = idx + 1
                else:
                    self.classifier.object_post_process(obj, None, None)
        post_processing_data = {}
        cv_image, tmp_objects_list, post_processing_data = self.objects_filtering.process(
            cv_image, tmp_objects_list, post_processing_data)
        cv_image, tmp_objects_list, post_processing_data = self.distance.process(
            cv_image, tmp_objects_list, post_processing_data)
        cv_image, tmp_objects_list, post_processing_data = self.anonymizer.process(
            cv_image, tmp_objects_list, post_processing_data)
        return cv_image, tmp_objects_list, post_processing_data.get("distances")

    def process_video(self, video_uri):
        self.detector = Detector(self.config)
        input_cap = cv.VideoCapture(video_uri)
        fps = max(25, input_cap.get(cv.CAP_PROP_FPS))

        if (input_cap.isOpened()):
            logger.info(f'opened video {video_uri}')
        else:
            logger.error(f'failed to load video {video_uri}')
            return

        self.running_video = True
        # enable logging gstreamer Errors (https://stackoverflow.com/questions/3298934/how-do-i-view-gstreamer-debug-output)
        os.environ['GST_DEBUG'] = "*:1"
        if self.live_feed_enabled:
            self.video_logger.start_logging(fps)
        dist_threshold = float(self.config.get_section_dict("PostProcessor")["DistThreshold"])
        frame_num = 0
        last_processed_time = time.time()
        while input_cap.isOpened() and self.running_video:
            _, cv_image = input_cap.read()
            if np.shape(cv_image) != ():
                if not self.live_feed_enabled and (time.time() - last_processed_time < self.log_time_interval):
                    continue
                cv_image, objects, distancings = self.__process(cv_image)
                violating_objects = extract_violating_objects(distancings, dist_threshold)
                if self.live_feed_enabled:
                    self.video_logger.update(cv_image, objects, distancings, violating_objects, self.detector.fps)
                last_processed_time = time.time()
                frame_num += 1
                if frame_num % 100 == 1:
                    logger.info(f'processed frame {frame_num} for {video_uri}')
                self.s3_logger.update(cv_image, objects, distancings, violating_objects, self.detector.fps)
                self.file_system_logger.update(cv_image, objects, distancings, violating_objects, self.detector.fps)
                self.web_hook_logger.update(cv_image, objects, distancings, violating_objects, self.detector.fps)

        input_cap.release()
        if self.live_feed_enabled:
            self.video_logger.stop_logging()
        del self.detector
        self.running_video = False

    def stop_process_video(self):
        self.running_video = False

    def update_history(self, tracks):
        """
        This method updates self.track_hist with new tracks
        """
        _new_track_hist = dict()
        prev_track_ids = list(self.track_hist.keys())
        for track in tracks:
            track_id = track[1]
            if track_id in prev_track_ids:
                prev_centroids = self.track_hist[track_id][0]
                prev_colors = self.track_hist[track_id][1]
                _new_track_hist[track_id] = (np.concatenate((prev_centroids, track[3][None, ...]), axis=0), prev_colors)
                if len(_new_track_hist[track_id][0]) > 50:
                    _new_track_hist[track_id] = (_new_track_hist[track_id][0][1:,:], _new_track_hist[track_id][1][1:])
            else:
                _new_track_hist[track_id] = (track[3][None, ...], [])
        self.track_hist = _new_track_hist
