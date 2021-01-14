import csv
import cv2 as cv
import logging
import numpy as np
import os

from datetime import date, datetime
from statistics import mean

from libs.classifiers.classifier import Classifier
from libs.trackers.tracker import Tracker
from libs.loggers.source_loggers.logger import Logger
from libs.detectors.detector import Detector
from libs.source_post_processors.source_post_processor import SourcePostProcessor


logger = logging.getLogger(__name__)
FRAMES_LOG_BATCH_SIZE = 100
LOG_SECTIONS = ["Detector", "Classifier", "Tracker", "Post processing steps"]
POST_PROCESSING = "Post processing steps"


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

        self.log_performance = self.config.get_boolean("App", "LogPerformanceMetrics")
        if self.log_performance:
            self.log_performance_directory = self.config.get_section_dict('App')['LogPerformanceMetricsDirectory']
            self.log_performance_headers = []
            self.last_log_time = None
            self.reset_log_detail(set_headers=bool(self.log_performance_directory))

    def __process(self, cv_image):
        """
        return object_list list of  dict for each obj,
        obj["bbox"] is normalized coordinations for [x0, y0, x1, y1] of box
        """

        # Resize input image to resolution
        cv_image = cv.resize(cv_image, self.resolution)

        # Execute detector
        begin_time = datetime.now()
        tmp_objects_list, detection_scores, class_ids, detection_bboxes, classifier_objects = self.detector.inference(cv_image)
        detector_time = (datetime.now() - begin_time).total_seconds()

        # Execute classifier and tracker
        if self.classifier:
            begin_time = datetime.now()
            classifier_results, classifier_scores = self.classifier.inference(classifier_objects)
            classifier_time = (datetime.now() - begin_time).total_seconds()

        begin_time = datetime.now()
        tracks = self.tracker.update(detection_bboxes, class_ids, detection_scores)
        tracker_time = (datetime.now() - begin_time).total_seconds()

        idx = 0
        for obj in tmp_objects_list:
            begin_time = datetime.now()
            self.tracker.object_post_process(obj, tracks)
            tracker_time += (datetime.now() - begin_time).total_seconds()

            if self.classifier is not None:
                begin_time = datetime.now()
                if obj.get("face") is not None:
                    self.classifier.object_post_process(obj, classifier_results[idx], classifier_scores[idx])
                    idx = idx + 1
                else:
                    self.classifier.object_post_process(obj, None, None)
                classifier_time += (datetime.now() - begin_time).total_seconds()

        # Execute post processors
        post_processing_data = {
            "tracks": tracks
        }
        for post_processor in self.post_processors:
            begin_time = datetime.now()
            cv_image, tmp_objects_list, post_processing_data = post_processor.process(
                cv_image, tmp_objects_list, post_processing_data)
            post_processors_time = (datetime.now() - begin_time).total_seconds()
            if self.log_performance:
                p_processor_name = post_processor.post_processor_name.replace("_", " ").title()
                self.log_detail["Post processing steps"][p_processor_name].append(post_processors_time)

        if self.log_performance:
            self.log_detail["Detector"].append(detector_time)
            if self.classifier:
                self.log_detail["Classifier"].append(classifier_time)
            self.log_detail["Tracker"].append(tracker_time)
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
                if frame_num % FRAMES_LOG_BATCH_SIZE == 1:
                    logger.info(f'processed frame {frame_num} for {video_uri}')
                    self.write_performance_log()
                for source_logger in self.loggers:
                    source_logger.update(cv_image, objects, post_processing_data, self.detector.fps)
        input_cap.release()
        for source_logger in self.loggers:
            source_logger.stop_logging()
        self.running_video = False

    def stop_process_video(self):
        self.running_video = False

    def reset_log_detail(self, set_headers=False):
        self.log_detail = {}
        if set_headers:
            self.log_performance_headers = ["Timestamp", "FPS"]
        for section in LOG_SECTIONS:
            if section == POST_PROCESSING:
                self.log_detail[section] = {}
                for p_processor in self.post_processors:
                    p_processor_name = p_processor.post_processor_name.replace("_", " ").title()
                    self.log_detail[section][p_processor_name] = []
                    if set_headers:
                        self.log_performance_headers.append(p_processor_name)
            else:
                self.log_detail[section] = []
                if set_headers:
                    self.log_performance_headers.append(section)

    def write_performance_log(self):
        if self.log_performance:
            if self.last_log_time:
                now = datetime.now()
                fps_time = FRAMES_LOG_BATCH_SIZE / (now - self.last_log_time).total_seconds()
                logger.info(f"FPS: {fps_time}")
                current_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
                csv_info = {
                    "Timestamp": current_time_str,
                    "FPS": str(fps_time)
                }
                for section in LOG_SECTIONS:
                    if isinstance(self.log_detail[section], list):
                        section_time = mean(self.log_detail[section])
                        logger.info(f"Average {section} time: {section_time}")
                        csv_info[section] = str(section_time)
                    else:
                        logger.info(f"{section}:")
                        for key, value in self.log_detail[section].items():
                            key_time = mean(value)
                            logger.info(f"  - Average {key} time: {key_time}")
                            csv_info[key] = str(key_time)
                if self.log_performance_directory:
                    os.makedirs(self.log_performance_directory, exist_ok=True)
                    file_name = str(date.today())
                    file_path = os.path.join(self.log_performance_directory, file_name + ".csv")
                    file_exists = os.path.isfile(file_path)
                    with open(file_path, "a") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=self.log_performance_headers)
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(csv_info)
        # Reset the performance log
        self.last_log_time = datetime.now()
        self.reset_log_detail()
