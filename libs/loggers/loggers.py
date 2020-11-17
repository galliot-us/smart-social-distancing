import itertools
import time

from datetime import datetime
from tools.environment_score import mx_environment_scoring_consider_crowd
from tools.objects_post_process import extract_violating_objects

from .web_hook_logger import WebHookLogger

LOG_FORMAT_VERSION = "1.0"


class Logger:
    """logger layer to build a logger and pass data to it for logging

    this class build a layer based on config specification and call update
    method of it based on logging frequency

        :param config: a ConfigEngine object which store all of the config parameters. Access  to any parameter
        is possible by calling get_section_dict method.
    """

    def __init__(self, config, camera_id):
        """build the logger and initialize the frame number and set attributes"""
        self.config = config
        # Logger name, at this time only csv_logger is supported. You can implement your own logger
        # by following csv_logger implementation as an example.
        self.name = self.config.get_section_dict("Logger")["Name"]
        self.loggers = []
        if self.name == "csv_logger":
            from .csv_logger import CSVLogger
            self.loggers.append(CSVLogger(self.config, camera_id))
        else:
            raise ValueError('Not supported logger named: ', self.name)

        if self.config.get_section_dict("Logger")["WebHooksEndpoint"]:
            self.loggers.append(WebHookLogger(self.config, camera_id))

        # Specifies how often the logger should log information. For example with time_interval of 0.5
        # the logger log the information every 0.5 seconds.
        self.time_interval = float(self.config.get_section_dict("Logger")["TimeInterval"])  # Seconds
        self.submited_time = 0
        self.dist_threshold = config.get_section_dict("PostProcessor")["DistThreshold"]

    def update(self, objects_list, distances):
        """call the update method of the logger.

        based on frame_number, fps and time interval, it decides whether to call the
        logger's update method to store the data or not.

        Args:
            objects_list: a list of dictionary where each dictionary stores information of an object (person) in a frame.
            distances: a 2-d numpy array that stores distance between each pair of objects.
        """

        if time.time() - self.submited_time > self.time_interval:
            # Get timeline which is used for as Timestamp
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S")
            # Process objects
            objects = self.format_objects(objects_list)
            violating_objects = extract_violating_objects(distances, self.dist_threshold)
            # Get unique objects that are in close contact
            violating_objects_index_list = list(set(itertools.chain(*violating_objects)))
            # Get the number of violating objects (people)
            violating_objects_count = len(violating_objects)
            # Get the number of detected objects (people)
            detected_objects_count = len(objects_list)
            # Get environment score
            environment_score = mx_environment_scoring_consider_crowd(detected_objects_count, violating_objects_count)
            for logger in self.loggers:
                logger.log_objects(
                    objects,
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
