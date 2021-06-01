import csv
import numpy as np
import os

from collections import deque
from datetime import date, datetime
from statistics import mean
from typing import Dict, Iterator, List

from .base import BaseMetric
from constants import OCCUPANCY


class OccupancyMetric(BaseMetric):

    reports_folder = OCCUPANCY
    csv_headers = ["AverageOccupancy", "MaxOccupancy", "OccupancyThreshold"]
    entity = "area"
    live_csv_headers = ["AverageOccupancy", "MaxOccupancy", "OccupancyThreshold", "Violations"]
    csv_default_values = [0, 0, 0, 0]

    @classmethod
    def process_metric_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        if not objects_logs[row_hour].get("Occupancy"):
            objects_logs[row_hour]["Occupancy"] = []
        objects_logs[row_hour]["Occupancy"].append(int(csv_row["Occupancy"]))

    @classmethod
    def generate_hourly_metric_data(cls, config, objects_logs, entity):
        summary = np.zeros((len(objects_logs), 3), dtype=np.long)
        now = datetime.now()
        for index, hour in enumerate(sorted(objects_logs)):
            start_hour_time = datetime(now.year, now.month, now.day, hour, 0)
            end_hour_time = datetime(now.year, now.month, now.day, hour, 59)
            occupancy_threshold = max(entity.get_occupancy_threshold(start_hour_time),
                                      entity.get_occupancy_threshold(end_hour_time))
            summary[index] = (
                mean(objects_logs[hour].get("Occupancy", [0])), max(objects_logs[hour].get("Occupancy", [0])),
                occupancy_threshold
            )
        return summary

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        average_ocupancy = []
        max_occupancy = []
        threshold = 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if int(row["AverageOccupancy"]):
                    average_ocupancy.append(int(row["AverageOccupancy"]))
                max_occupancy.append(int(row["MaxOccupancy"]))
                threshold = max(int(row["OccupancyThreshold"]), threshold)
        if not average_ocupancy:
            return 0, 0, threshold
        return round(mean(average_ocupancy), 2), max(max_occupancy), threshold

    @classmethod
    def generate_live_csv_data(cls, config, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """

        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            last_entries = deque(csv.DictReader(log), entries_in_interval)
            for entry in last_entries:
                cls.process_csv_row(entry, objects_logs, None)
            # Put the rows in the same hour
            objects_logs_merged = {
                0: {"Occupancy": []}
            }
            for hour in objects_logs:
                objects_logs_merged[0]["Occupancy"].extend(objects_logs[hour]["Occupancy"])
        occupancy_live = cls.generate_hourly_metric_data(config, objects_logs_merged, entity)[0].tolist()
        daily_violations = 0
        entity_directory = entity.base_directory
        reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
        file_path = os.path.join(reports_directory, "live.csv")
        if os.path.exists(file_path):
            with open(file_path, "r") as live_file:
                last_entry = deque(csv.DictReader(live_file), 1)[0]
                if datetime.strptime(last_entry["Time"], "%Y-%m-%d %H:%M:%S").date() == datetime.today().date():
                    daily_violations = int(last_entry["Violations"])
        if occupancy_live[1] > occupancy_live[2]:
            # Max Occupancy detections > Occupancy threshold
            daily_violations += 1
        occupancy_live.append(daily_violations)
        return occupancy_live

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        latest_occupancy_results = {}
        for n in range(10):
            latest_occupancy_results[n] = None
        for live_path in live_report_paths:
            with open(live_path, "r") as live_file:
                lastest_10_entries = deque(csv.DictReader(live_file), 10)
                for index, item in enumerate(lastest_10_entries):
                    if not latest_occupancy_results[index]:
                        latest_occupancy_results[index] = 0
                    latest_occupancy_results[index] += int(item["MaxOccupancy"])
        return [item for item in latest_occupancy_results.values() if item is not None]

    @classmethod
    def get_weekly_report(cls, entities: List[str], number_of_weeks: int = 0,
                          from_date: date = None, to_date: date = None) -> Dict:
        # The occupancy metrics can not be aggregated using "sum"
        weekly_report_data = cls.generate_weekly_report_data(entities, number_of_weeks, from_date, to_date)
        report = {"Weeks": []}
        for header in cls.csv_headers:
            report[header] = []
        for week, week_data in weekly_report_data.items():
            report["Weeks"].append(week)
            report["AverageOccupancy"].append(round(mean(week_data["AverageOccupancy"]), 2))
            report["MaxOccupancy"].append(max(week_data["MaxOccupancy"]))
            report["OccupancyThreshold"].append(max(week_data["OccupancyThreshold"]))
        return report
