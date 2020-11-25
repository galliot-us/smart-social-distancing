import cv2 as cv
import logging
import numpy as np
import os
import time
from libs.classifiers.classifier import Classifier
from libs.trackers.tracker import Tracker
from libs.loggers.logger import Logger
from libs.detectors.detector import Detector
from libs.source_post_processors.source_post_processor import SourcePostProcessor

logger = logging.getLogger(__name__)


class CvEngine:

    def __init__(self, config, source, live_feed_enabled=True):
        self.config = config
        self.live_feed_enabled = live_feed_enabled
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])
        self.track_hist = dict()

        # Init detector, tracker and classifier
        self.detector = Detector(self.config)
        self.tracker = Tracker(self.config)
        self.classifier = None

        if "Classifier" in self.config.get_sections():
            self.classifier = Classifier(self.config)

        # Init post processors
        self.post_processors = []
        post_processors_names = [x for x in self.config.get_sections() if x.startswith("SourcePostProcessor_")]
        for p_name in post_processors_names:
            self.post_processors.append(SourcePostProcessor(self.config, source, p_name))

        # Init loggers
        self.loggers = []
        loggers_names = [x for x in self.config.get_sections() if x.startswith("SourceLogger_")]
        self.log_time_interval = None
        for l_name in loggers_names:
            self.loggers.append(Logger(self.config, source, l_name, self.live_feed_enabled))
            if self.config.get_section_dict(l_name).get("TimeInterval"):
                if not self.log_time_interval:
                    self.log_time_interval = float(self.config.get_section_dict(l_name).get("TimeInterval"))
                else:
                    self.log_time_interval = min(
                        self.log_time_interval, float(self.config.get_section_dict(l_name).get("TimeInterval")))

        self.running_video = False

    def __process(self, cv_image):
        """
        return object_list list of  dict for each obj,
        obj["bbox"] is normalized coordinations for [x0, y0, x1, y1] of box
        """

        # Resize input image to resolution
        cv_image = cv.resize(cv_image, self.resolution)

        # Execute detector
        tmp_objects_list, detection_scores, class_ids, detection_bboxes, classifier_objects = self.detector.inference(cv_image)

        # Execute classifier and tracker
        if self.classifier:
            classifier_results, classifier_scores = self.classifier.inference(classifier_objects)
        tracks = self.tracker.update(detection_bboxes, class_ids, detection_scores)
        self.update_history(tracks)
        idx = 0
        for obj in tmp_objects_list:
            self.tracker.object_post_process(obj, tracks)
            if self.classifier is not None:
                if obj.get("face") is not None:
                    self.classifier.object_post_process(obj, classifier_results[idx], classifier_scores[idx])
                    idx = idx + 1
                else:
                    self.classifier.object_post_process(obj, None, None)

        # Execute post processors
        post_processing_data = {}
        for post_processor in self.post_processors:
            cv_image, tmp_objects_list, post_processing_data = post_processor.process(
                cv_image, tmp_objects_list, post_processing_data)
        return cv_image, tmp_objects_list, post_processing_data

    def process_video(self, video_uri):
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

        for source_logger in self.loggers:
            source_logger.start_logging(fps)

        frame_num = 0
        last_processed_time = time.time()
        while input_cap.isOpened() and self.running_video:
            _, cv_image = input_cap.read()
            if np.shape(cv_image) != ():
                if not self.live_feed_enabled and (time.time() - last_processed_time < self.log_time_interval):
                    continue
                cv_image, objects, post_processing_data = self.__process(cv_image)
                last_processed_time = time.time()
                frame_num += 1
                if frame_num % 100 == 1:
                    logger.info(f'processed frame {frame_num} for {video_uri}')
                for source_logger in self.loggers:
                    source_logger.update(cv_image, objects, post_processing_data, self.detector.fps)
        input_cap.release()
        for source_logger in self.loggers:
            source_logger.stop_logging()
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
