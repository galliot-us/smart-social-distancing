import cv2 as cv
import logging
import numpy as np
import os
from libs.classifiers.classifier import Classifier
from libs.trackers.tracker import Tracker
from libs.loggers.source_loggers.logger import Logger
from libs.detectors.detector import Detector
from libs.source_post_processors.source_post_processor import SourcePostProcessor

logger = logging.getLogger(__name__)


class CvEngine:

    def __init__(self, config, source):
        self.config = config
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])

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
            if self.config.get_boolean(p_name, "Enabled"):
                self.post_processors.append(SourcePostProcessor(self.config, source, p_name))

        # Init loggers
        self.loggers = []
        loggers_names = [x for x in self.config.get_sections() if x.startswith("SourceLogger_")]
        for l_name in loggers_names:
            if self.config.get_boolean(l_name, "Enabled"):
                self.loggers.append(Logger(self.config, source, l_name))
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
        post_processing_data = {
            "tracks": tracks
        }
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
        while input_cap.isOpened() and self.running_video:
            _, cv_image = input_cap.read()
            if np.shape(cv_image) != ():
                cv_image, objects, post_processing_data = self.__process(cv_image)
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
