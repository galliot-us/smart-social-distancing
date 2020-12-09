import csv
import ast
import numpy as np
import os

from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple

from libs.utils.loggers import get_source_log_directory

from .base import BaseMetric


class SocialDistancingMetric(BaseMetric):

    reports_folder = "social-distancing"
    csv_headers = ["Number", "DetectedObjects", "ViolatingObjects"]

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
                index in ast.literal_eval(csv_row["ViolationsIndexes"]))

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs):
        summary = np.zeros((len(objects_logs), 3), dtype=np.long)
        for index, hour in enumerate(sorted(objects_logs)):
            hour_objects_detections = objects_logs[hour]
            for detection_object in hour_objects_detections.values():
                object_detections, object_violations = cls.process_distance_violation_for_object(
                    detection_object["distance_violations"])
                summary[index] += (1, object_detections, object_violations)
        return summary

    @classmethod
    def process_distance_violation_for_object(cls, distance_violations: List[bool]) -> Tuple[int, int]:
        """
        Receives a list with the "social distancing detections" (for a single person) and returns a
        tuple with the summary of detections and violations. Consecutive detections in the same state are
        grouped and returned as a single one. Detections lower than the constant PROCESSING_COUNT_THRESHOLD
        are ignored.

        For example, the input [True, True, True, True, True, True, False, True, True, True, True, True, False,
        False, False, False, False, False, True, True, True, True, True] returns (3, 2).
        """
        # TODO: This is the first version of the metrics and is implemented to feed the current dashboard.
        # When we define the new metrics we will need to change that logic
        object_detections = 0
        object_violations = 0
        current_status = None
        processing_status = None
        processing_count = 0

        for dist_violation in distance_violations:
            if processing_status != dist_violation:
                processing_status = dist_violation
                processing_count = 0
            processing_count += 1
            if current_status != processing_status and processing_count >= cls.processing_count_threshold:
                # Object was enouth time in the same state, change it
                current_status = processing_status
                object_detections += 1
                if current_status:
                    # The object was violating the social distance, report it
                    object_violations += 1
        return object_detections, object_violations

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        total_number, total_detections, total_violations = 0, 0, 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_number += int(row["Number"])
                total_detections += int(row["DetectedObjects"])
                total_violations += int(row["ViolatingObjects"])
        return total_number, total_detections, total_violations

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
