import csv
import ast
import numpy as np
import os

from collections import deque
from datetime import datetime, date, timedelta
from typing import Dict, List, Iterator, Tuple

from libs.utils.loggers import get_source_log_directory

from .base import BaseMetric


class SocialDistancingMetric(BaseMetric):

    reports_folder = "social-distancing"
    csv_headers = ["DetectedObjects", "NoInfringement", "LowInfringement", "HighInfringement",
                   "CriticalInfringement"]

    @classmethod
    def procces_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        for index, d in enumerate(detections):
            if not objects_logs[row_hour].get(d["tracking_id"]):
                objects_logs[row_hour][d["tracking_id"]] = {"distance_violations": []}
            # Append social distancing violations
            objects_logs[row_hour][d["tracking_id"]]["distance_violations"].append(
                {
                    "time": row_time,
                    "infrigement": index in ast.literal_eval(csv_row["ViolationsIndexes"])
                }
            )

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs):
        summary = np.zeros((len(objects_logs), 5), dtype=np.long)
        for index, hour in enumerate(sorted(objects_logs)):
            hour_objects_detections = objects_logs[hour]
            for detection_object in hour_objects_detections.values():
                summary[index] += cls.process_distance_violation_for_object(
                    detection_object["distance_violations"])
        return summary

    @classmethod
    def process_distance_violation_for_object(cls, distance_violations: List[dict]) -> Tuple[int, int]:
        """
        Receives a list with the "social distancing detections" (for a single person) and returns a
        tuple with the summary of detections and violations (grouped by severity). Consecutive detections in
        the same state are grouped and returned as a single one. Detections lower than the constant
        PROCESSING_COUNT_THRESHOLD are ignored.

        The infrigement categories are :
            - Low: Between 10 seconds 30 seconds
            - High: Between 30 and 60 seconds
            - Critical: More than 60 seconds
        """
        # TODO: The categories values defined need to be updated taking into account the OMS recommendations.
        # The current values only have demo purposes
        current_status = None
        processing_status = None
        processing_count = 0
        processing_time = None

        CRITICAL_THRESHOLD = 60
        HIGH_THRESHOLD = 30
        LOW_TRESHOLD = 10

        detections = []
        if distance_violations:
            for dist_violation in distance_violations:
                status = dist_violation["infrigement"]
                if processing_status != status:
                    processing_status = status
                    processing_time = dist_violation["time"]
                    processing_count = 0
                processing_count += 1
                if current_status != processing_status and processing_count >= cls.processing_count_threshold:
                    # Object was enouth time in the same state, change it
                    if current_status is not None:
                        # Append the previous status in the detections list
                        seconds_in_status = (dist_violation["time"] - processing_time).seconds
                        detections.append({"status": status, "seconds": seconds_in_status})
                    current_status = processing_status
                    processing_time = dist_violation["time"]
            # Append the latest status
            seconds_in_status = (distance_violations[-1]["time"] - processing_time).seconds
            detections.append({"status": status, "seconds": seconds_in_status})
        detected_objects, no_infringements, low_infringements, high_infringements, critical_infringements = 0, 0, 0, 0, 0
        for detection in detections:
            detected_objects += 1
            if not detection["status"] or detection["seconds"] < LOW_TRESHOLD:
                no_infringements += 1
            elif LOW_TRESHOLD <= detection["seconds"] < HIGH_THRESHOLD:
                low_infringements += 1
            elif HIGH_THRESHOLD <= detection["seconds"] < CRITICAL_THRESHOLD:
                high_infringements += 1
            else:
                # CRITICAL_THRESHOLD <= detection["time"]
                critical_infringements += 1

        return detected_objects, no_infringements, low_infringements, high_infringements, critical_infringements

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        detected_objects, no_infringements, low_infringements, high_infringements, critical_infringements = 0, 0, 0, 0, 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                detected_objects += int(row["DetectedObjects"])
                no_infringements += int(row["NoInfringement"])
                low_infringements += int(row["LowInfringement"])
                high_infringements += int(row["HighInfringement"])
                critical_infringements += int(row["CriticalInfringement"])
        return detected_objects, no_infringements, low_infringements, high_infringements, critical_infringements

    @classmethod
    def create_heatmap_report(cls, config, yesterday_csv, heatmap_file, column):
        heatmap_resolution = config.get_section_dict("App")["HeatmapResolution"].split(",")
        heatmap_x = int(heatmap_resolution[0])
        heatmap_y = int(heatmap_resolution[1])
        heatmap_grid = np.zeros((heatmap_x, heatmap_y))

        with open(yesterday_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                detections = ast.literal_eval(row['Detections'])
                if column == 'Violations':
                    violations_indexes = ast.literal_eval(row['ViolationsIndexes'])
                    # Get bounding boxes of violations
                    detections = [detections[object_id] for object_id in violations_indexes]

                for detection in detections:
                    bbox = detection.get('bbox')
                    x = int((np.floor((bbox[0] + bbox[2]) * heatmap_x / 2)).item())
                    y = int((np.floor((bbox[1] + bbox[3]) * heatmap_y / 2)).item())
                    heatmap_grid[x][y] += 1 / (1 + heatmap_grid[x][y])
            np.save(heatmap_file, heatmap_grid)

    @classmethod
    def compute_daily_metrics(cls, config):
        super().compute_daily_metrics(config)
        base_directory = get_source_log_directory(config)
        entities = config.get_video_sources()
        for entity in entities:
            entity_directory = os.path.join(base_directory, entity["id"])
            objects_log_directory = os.path.join(entity_directory, "objects_log")
            heatmaps_directory = os.path.join(entity_directory, "heatmaps")
            # Create missing directories
            os.makedirs(objects_log_directory, exist_ok=True)
            os.makedirs(heatmaps_directory, exist_ok=True)
            yesterday = str(date.today() - timedelta(days=1))
            yesterday_csv = os.path.join(objects_log_directory, yesterday + ".csv")
            detection_heatmap_file = os.path.join(heatmaps_directory, "detections_heatmap_" + yesterday)
            violation_heatmap_file = os.path.join(heatmaps_directory, "violations_heatmap_" + yesterday)
            cls.create_heatmap_report(config, yesterday_csv, detection_heatmap_file, "Detections")
            cls.create_heatmap_report(config, yesterday_csv, violation_heatmap_file, "Violations")

    @classmethod
    def generate_live_csv_data(cls, today_entity_csv, entity):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            lastest_entries = deque(csv.DictReader(log), 1000)
            for entry in lastest_entries:
                cls.procces_csv_row(entry, objects_logs)
        return np.sum(cls.generate_hourly_metric_data(objects_logs), axis=0)

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        latest_social_distancing_results = {}
        for n in range(10):
            latest_social_distancing_results[n] = None
        for live_path in live_report_paths:
            with open(live_path, "r") as live_file:
                lastest_10_entries = deque(csv.DictReader(live_file), 10)
                for index, item in enumerate(lastest_10_entries):
                    if not latest_social_distancing_results[index]:
                        latest_social_distancing_results[index] = 0
                    latest_social_distancing_results[index] += int(item["DetectedObjects"]) - int(item["NoInfringement"])
        return [item for item in latest_social_distancing_results.values() if item is not None]
