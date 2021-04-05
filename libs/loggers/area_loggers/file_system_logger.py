import csv
import os

from datetime import date, datetime
from typing import List

from constants import ALL_AREAS


class FileSystemLogger:

    def __init__(self, config, area: str, logger: str):
        self.config = config
        if area == ALL_AREAS:
            self.area_id = ALL_AREAS
        else:
            self.area_id = self.config.get_section_dict(area)["Id"]
        self.log_directory = config.get_section_dict(logger)["LogDirectory"]
        self.occupancy_log_directory = os.path.join(self.log_directory, self.area_id, "occupancy_log")
        os.makedirs(self.occupancy_log_directory, exist_ok=True)
        self.submited_time = 0

    def update(self, cameras: List[str], area_data: dict):
        file_name = str(date.today())
        file_path = os.path.join(self.occupancy_log_directory, file_name + ".csv")
        file_exists = os.path.isfile(file_path)
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")

        with open(file_path, "a") as csvfile:
            headers = ["Timestamp", "Cameras", "Occupancy"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
            writer.writerow(
                {"Timestamp": current_time, "Cameras": cameras, "Occupancy": area_data["occupancy"]})
