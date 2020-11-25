import itertools
import logging
import requests
import time

from datetime import datetime
from requests.exceptions import ConnectionError

from tools.environment_score import mx_environment_scoring_consider_crowd

LOG_FORMAT_VERSION = "1.0"
logger = logging.getLogger(__name__)


class WebHookLogger:

    def __init__(self, config, source: str, logger: str, live_feed_enabled: bool):
        self.config = config
        self.camera_id = self.config.get_section_dict(source)['Id']
        self.web_hook_endpoint = config.get_section_dict(logger)["Endpoint"]
        self.time_interval = float(self.config.get_section_dict(logger)["TimeInterval"])  # Seconds
        self.submited_time = 0

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        request_data = {
            "version": version,
            "timestamp": time_stamp,
            "detected_objects": detected_objects_cout,
            "violating_objects": violating_objects_count,
            "environment_score": environment_score,
            "detections": str(objects),
            "violations_indexes": str(violating_objects_index_list)
        }
        try:
            requests.put(self.web_hook_endpoint, data=request_data)
        except ConnectionError:
            logger.error(f"Connection with endpoint {self.web_hook_endpoint} can't be established")

    def update(self, cv_image, objects, post_processing_data, fps):
        violating_objects = post_processing_data.get("violating_objects", [])
        if not self.web_hook_endpoint:
            return
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
