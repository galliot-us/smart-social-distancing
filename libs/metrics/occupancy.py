import csv
import numpy as np

from datetime import datetime
from statistics import mean
from typing import Dict

from .base import BaseMetric


class OccupancyMetric(BaseMetric):

    reports_folder = "occupancy"
    csv_headers = ["AverageOccupancy", "MaxOccupancy"]
    entity = "area"

    @classmethod
    def procces_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        row_hour = row_time.hour
        if not objects_logs[row_hour].get("Occupancy"):
            objects_logs[row_hour]["Occupancy"] = []
        objects_logs[row_hour]["Occupancy"].append(int(csv_row["Occupancy"]))

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs):
        summary = np.zeros((len(objects_logs), 2), dtype=np.long)
        for index, hour in enumerate(sorted(objects_logs)):
            summary[index] = (
                mean(objects_logs[hour].get("Occupancy", [0])), max(objects_logs[hour].get("Occupancy", [0]))
            )
        return summary

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        average_ocupancy = []
        max_occupancy = []
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row["AverageOccupancy"]):
                    average_ocupancy.append(int(row["AverageOccupancy"]))
                max_occupancy.append(int(row["MaxOccupancy"]))
        if not average_ocupancy:
            return 0, 0
        return round(mean(average_ocupancy), 2), max(max_occupancy)
