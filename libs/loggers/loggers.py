import time

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
        if self.name == "csv_logger":
            from . import csv_processed_logger
            self.logger = csv_processed_logger.Logger(self.config, camera_id)

            # For Logger instance from loggers/csv_logger
            # region csv_logger
            # from . import csv_logger
            # self.logger = csv_logger.Logger(self.config)
            # end region

        # Specifies how often the logger should log information. For example with time_interval of 0.5
        # the logger log the information every 0.5 seconds.
        self.time_interval = float(self.config.get_section_dict("Logger")["TimeInterval"])  # Seconds
        self.submited_time = 0
        # self.frame_number = 0  # For Logger instance from loggers/csv_logger

    def update(self, objects_list, distances):
        """call the update method of the logger.

        based on frame_number, fps and time interval, it decides whether to call the
        logger's update method to store the data or not.

        Args:
            objects_list: a list of dictionary where each dictionary stores information of an object (person) in a frame.
            distances: a 2-d numpy array that stores distance between each pair of objects.
        """

        if time.time() - self.submited_time > self.time_interval:
            objects = self.format_objects(objects_list)
            self.logger.update(objects, distances, version=LOG_FORMAT_VERSION)
            self.submited_time = time.time()
            # For Logger instance from loggers/csv_logger
            # region
            # self.logger.update(self.frame_number, objects_list, distances)
            # self.frame_number += 1
            # end region

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
