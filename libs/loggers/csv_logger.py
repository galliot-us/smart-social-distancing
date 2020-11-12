import csv
import os
from datetime import date

from .logger_template import LoggerTemplate


class CSVLogger(LoggerTemplate):
    """A CSV logger class that store objects information and violated distances information into csv files.

    This logger creates two csv file every day in two different directory, one for logging detected objects
    and violated social distancing incidents. The file names are the same as recording date.

    :param config: A ConfigEngine object which store all of the config parameters. Access to any parameter
        is possible by calling get_section_dict method.
    """

    def __init__(self, config, camera_id):
        self.config = config
        # The parent directory that stores all log file.
        self.log_directory = config.get_section_dict("Logger")["LogDirectory"]
        # A directory inside the log_directory that stores object log files.
        self.objects_log_directory = os.path.join(self.log_directory, camera_id, "objects_log")

        os.makedirs(self.objects_log_directory, exist_ok=True)

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
                {'Version': version, 'Timestamp': time_stamp, 'DetectedObjects': detected_objects_cout,
                 'ViolatingObjects': violating_objects_count, 'EnvironmentScore': environment_score,
                 'Detections': str(objects), 'ViolationsIndexes': str(violating_objects_index_list)})
