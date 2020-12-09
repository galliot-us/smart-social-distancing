
import ast
import csv
import numpy as np

from datetime import datetime
from typing import Dict, List, Tuple

from .base import BaseMetric


class FaceMaskUsageMetric(BaseMetric):

    reports_folder = "face-mask-usage"
    csv_headers = ["DetectedFaces", "UsingFacemask"]

    @classmethod
    def procces_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        for d in detections:
            if not objects_logs[row_hour].get(d["tracking_id"]):
                objects_logs[row_hour][d["tracking_id"]] = {"face_labels": []}
            # Append social distancing violations
            objects_logs[row_hour][d["tracking_id"]]["face_labels"].append(d.get("face_label", -1))

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs):
        summary = np.zeros((len(objects_logs), 2), dtype=np.long)
        for index, hour in enumerate(sorted(objects_logs)):
            hour_objects_detections = objects_logs[hour]
            for detection_object in hour_objects_detections.values():
                face_detections, mask_detections = cls.process_face_labels_for_object(detection_object["face_labels"])
                summary[index] += (face_detections, mask_detections)
        return summary

    @classmethod
    def process_face_labels_for_object(cls, face_labels: List[int]) -> Tuple[int, int]:
        """
        Receives a list with the "facesmask detections" (for a single person) and returns a
        tuple with the summary of faces and mask detected. Consecutive detections in the same state are
        grouped and returned as a single one. Detections lower than the constant PROCESSING_COUNT_THRESHOLD
        are ignored.

        For example, the input [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1 1, 1,
        -1, -1, -1, -1, -1, -1, 0, 0, 0, 0] returns (3, 2).
        """
        # TODO: This is the first version of the metrics and is implemented to feed the current dashboard.
        # When we define the new metrics we will need to change that logic
        face_detections = 0
        mask_detections = 0
        current_status = None
        processing_status = None
        processing_count = 0

        for face_label in face_labels:
            if processing_status != face_label:
                processing_status = face_label
                processing_count = 0
            processing_count += 1
            if current_status != processing_status and processing_count >= cls.processing_count_threshold:
                # FaceLabel was enouth time in the same state, change it
                current_status = processing_status
                if current_status != -1:
                    # A face was detected
                    face_detections += 1
                if current_status == 0:
                    # A mask was detected
                    mask_detections += 1
        return face_detections, mask_detections

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        total_faces, total_masks = 0, 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_faces += int(row["DetectedFaces"])
                total_masks += int(row["UsingFacemask"])
        return total_faces, total_masks
