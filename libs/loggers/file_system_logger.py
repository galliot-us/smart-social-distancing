import csv
import logging
import itertools
import os
import time

import cv2 as cv
from datetime import date, datetime

from tools.environment_score import mx_environment_scoring_consider_crowd

LOG_FORMAT_VERSION = "1.0"
logger = logging.getLogger(__name__)


class FileSystemLogger:

    def __init__(self, config, source: str, logger: str, live_feed_enabled: bool):
        self.config = config
        self.camera_id = self.config.get_section_dict(source)['Id']

        self.time_interval = float(self.config.get_section_dict(logger)["TimeInterval"])  # Seconds
        self.submited_time = 0
        self.log_directory = config.get_section_dict(logger)["LogDirectory"]
        self.objects_log_directory = os.path.join(self.log_directory, self.camera_id, "objects_log")
        os.makedirs(self.objects_log_directory, exist_ok=True)

        self.screenshot_period = float(self.config.get_section_dict(logger)["ScreenshotPeriod"]) * 60
        self.start_time = time.time()
        # config.ini uses minutes as unit
        self.screenshot_path = os.path.join(self.config.get_section_dict("App")["ScreenshotsDirectory"], self.camera_id)
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)

    def save_screenshot(self, cv_image):
        dir_path = f'{self.screenshot_path}/default.jpg'
        if not os.path.exists(dir_path):
            logger.info(f"Saving default screenshot for {self.camera_id}")
            cv.imwrite(f'{self.screenshot_path}/default.jpg', cv_image)

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        file_name = str(date.today())
        file_path = os.path.join(self.objects_log_directory, file_name + ".csv")
        file_exists = os.path.isfile(file_path)
        with open(file_path, "a") as csvfile:
            headers = ["Version", "Timestamp", "DetectedObjects", "ViolatingObjects",
                       "EnvironmentScore", "Detections", 'ViolationsIndexes']
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {"Version": version, "Timestamp": time_stamp, "DetectedObjects": detected_objects_cout,
                 "ViolatingObjects": violating_objects_count, "EnvironmentScore": environment_score,
                 "Detections": str(objects), "ViolationsIndexes": str(violating_objects_index_list)})

    def update(self, cv_image, objects, post_processing_data, fps):
        violating_objects = post_processing_data.get("violating_objects", [])
        # Save a screenshot only if the period is greater than 0, a violation is detected, and the minimum period
        # has occured
        if (self.screenshot_period > 0) and (time.time() > self.start_time + self.screenshot_period) and (
                len(violating_objects) > 0):
            self.start_time = time.time()
            self.save_screenshot(cv_image)
        if time.time() - self.submited_time > self.time_interval:
            # Get timeline which is used for as Timestamp
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            # Process objects
            objects_formated = self.format_objects(objects)
            # Get unique objects that are in close contact
            violating_objects_index_list = list(set(itertools.chain(*violating_objects)))
            # Get the number of violating objects (people)
            violating_objects_count = len(violating_objects)
            # Get the number of detected objects (people)
            detected_objects_count = len(objects)
            # Get environment score
            environment_score = mx_environment_scoring_consider_crowd(detected_objects_count, violating_objects_count)
            self.log_objects(
                objects_formated,
                violating_objects,
                violating_objects_index_list,
                violating_objects_count,
                detected_objects_count,
                environment_score,
                current_time,
                version=LOG_FORMAT_VERSION
            )
            self.submited_time = time.time()

    def format_objects(self, objects_list):
        """ Format the attributes of the objects in a way ready to be saved

            Args:
                objects_list: a list of dictionary where each dictionary stores information of an object (person) in a frame.
        """
        objects = []
        for obj_dict in objects_list:
            obj = {}
            # TODO: Get 3D position of objects
            obj["position"] = [0.0, 0.0, 0.0]
            obj["bbox"] = obj_dict["bbox"]
            obj["tracking_id"] = obj_dict["id"]
            if "face_label" in obj_dict and obj_dict["face_label"] != -1:
                obj["face_label"] = obj_dict["face_label"]
            # TODO: Add more optional parameters
            objects.append(obj)
        return objects

    def start_logging(self, fps):
        pass

    def stop_logging(self):
        pass
