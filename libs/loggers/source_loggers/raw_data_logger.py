import logging
import itertools
import time

from datetime import datetime

from tools.environment_score import mx_environment_scoring_consider_crowd

LOG_FORMAT_VERSION = "1.0"
logger = logging.getLogger(__name__)


class RawDataLogger:

    def __init__(self, config, source: str, logger: str):
        self.config = config
        self.camera_id = self.config.get_section_dict(source)["Id"]
        self.time_interval = float(self.config.get_section_dict(logger)["TimeInterval"])  # Seconds
        self.submited_time = 0

    def log_objects(self, objects, violating_objects, violating_objects_index_list, violating_objects_count,
                    detected_objects_cout, environment_score, time_stamp, version):
        raise NotImplementedError

    def update(self, cv_image, objects, post_processing_data, fps, log_time):
        violating_objects = post_processing_data.get("violating_objects", [])
        if not log_time:
            now = datetime.now()
            log_time = now.strftime("%Y-%m-%d %H:%M:%S")
            if time.time() - self.submited_time < self.time_interval:
                return
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
            log_time,
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
            obj["bbox_real"] = obj_dict["bboxReal"]
            obj["bbox"] = obj_dict["bbox"]
            obj["tracking_id"] = obj_dict.get("tracked_id", obj_dict["id"])
            if "face_label" in obj_dict and obj_dict["face_label"] != -1:
                obj["face_label"] = obj_dict["face_label"]
            # TODO: Add more optional parameters
            objects.append(obj)
        return objects

    def start_logging(self, fps):
        pass

    def stop_logging(self):
        pass
