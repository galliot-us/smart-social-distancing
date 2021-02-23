import ast
import csv
import json
import os
import numpy as np

from collections import deque
from datetime import date
from typing import Dict, Iterator, List
from datetime import datetime

from .base import BaseMetric
from constants import IN_OUT
from libs.utils.config import get_source_config_directory
from libs.utils.utils import validate_file_exists_and_is_not_empty


class InOutMetric(BaseMetric):

    reports_folder = IN_OUT
    csv_headers = ["In", "Out"]

    @classmethod
    def process_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")

        # csv_row
        #
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        for d in detections:
            # print(d["track_info"]["track_history"])
            if not objects_logs[row_hour].get(d["tracking_id"]):
                objects_logs[row_hour][d["tracking_id"]] = {"face_labels": []}
            # Append social distancing violations
            objects_logs[row_hour][d["tracking_id"]]["face_labels"].append(d.get("face_label", -1))

    @classmethod
    def generate_hourly_metric_data(cls, objects_logs, entity):
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def generate_live_csv_data(cls, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            lastest_entries = deque(csv.DictReader(log), entries_in_interval)
            detection_entries = [ast.literal_eval(entry["Detections"]) for entry in lastest_entries]
            paths = {}
            for entry in detection_entries:
                for detection in entry:
                    track_id = detection["tracking_id"]
                    corners = detection["bbox_real"]
                    x1, x2 = int(corners[0]), int(corners[2])
                    y1, y2 = int(corners[1]), int(corners[3])
                    position = (x1 + (x2 - x1) / 2, y2)
                    if not track_id in paths:
                        paths[track_id] = [position]
                    else:
                        paths[track_id].append(position)
            print(paths)
            # unique_objects = [entry[], entry["Detections"] for entry in lastest_entries]
            # for entry in lastest_entries:
                # cls.process_csv_row(entry, objects_logs)
        return 0
        return np.sum(cls.generate_hourly_metric_data(objects_logs), axis=0)
        occupancy_live = cls.generate_hourly_metric_data(objects_logs_merged, entity)[0].tolist()
        occupancy_live.append(int(entity["occupancy_threshold"]))
        daily_violations = 0
        entity_directory = entity["base_directory"]
        reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
        file_path = os.path.join(reports_directory, "live.csv")
        if os.path.exists(file_path):
            with open(file_path, "r") as live_file:
                lastest_entry = deque(csv.DictReader(live_file), 1)[0]
                if datetime.strptime(lastest_entry["Time"], "%Y-%m-%d %H:%M:%S").date() == datetime.today().date():
                    daily_violations = int(lastest_entry["Violations"])
        if occupancy_live[1] > occupancy_live[2]:
            # Max Occupancy detections > Occupancy threshold
            daily_violations += 1
        occupancy_live.append(daily_violations)
        return occupancy_live

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def get_weekly_report(cls, entities: List[str], number_of_weeks: int = 0,
                          from_date: date = None, to_date: date = None) -> Dict:
        raise NotImplementedError("Operation not implemented")

    @classmethod
    def get_in_out_file_path(cls, camera_id, config):
        """ Returns the path to the roi_contour file """
        return f"{get_source_config_directory(config)}/{camera_id}/{IN_OUT}/{IN_OUT}.json"

    @classmethod
    def get_in_out_boundaries(cls, in_out_file_path):
        """ Given the path to the in-out file it loads it and returns it """
        if validate_file_exists_and_is_not_empty(in_out_file_path):
            with open(in_out_file_path) as json_file:
                in_out_boundaries = json.load(json_file)
            return in_out_boundaries
        else:
            return None

# From https://github.com/yas-sim/object-tracking-line-crossing-area-intrusion/blob/master/object-detection-and-line-cross.py

# Multiple lines cross check
def checkLineCrosses(boundaryLines, objects):
    for obj in objects:
        traj = obj.trajectory
        if len(traj) > 1:
            p0 = traj[-2]
            p1 = traj[-1]
            for line in boundaryLines:
                checkLineCross(line, [p0[0], p0[1], p1[0], p1[1]])

# in: boundary_line = boundaryLine class object
#     trajectory   = (x1, y1, x2, y2)
def checkLineCross(boundary_line, trajectory):
    traj_p0 = (trajectory[0], trajectory[1])  # Trajectory of an object
    traj_p1 = (trajectory[2], trajectory[3])
    bLine_p0 = (boundary_line.p0[0], boundary_line.p0[1])  # Boundary line
    bLine_p1 = (boundary_line.p1[0], boundary_line.p1[1])
    intersect = checkIntersect(traj_p0, traj_p1, bLine_p0, bLine_p1)  # Check if intersect or not
    if intersect == True:
        angle = calcVectorAngle(traj_p0, traj_p1, bLine_p0,
                                bLine_p1)  # Calculate angle between trajectory and boundary line
        if angle < 180:
            boundary_line.count1 += 1
        else:
            boundary_line.count2 += 1
        # cx, cy = calcIntersectPoint(traj_p0, traj_p1, bLine_p0, bLine_p1) # Calculate the intersect coordination

# Check if line segments intersect - 線分同士が交差するかどうかチェック
def checkIntersect(p1, p2, p3, p4):
    tc1 = (p1[0] - p2[0]) * (p3[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p3[0])
    tc2 = (p1[0] - p2[0]) * (p4[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p4[0])
    td1 = (p3[0] - p4[0]) * (p1[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p1[0])
    td2 = (p3[0] - p4[0]) * (p2[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p2[0])
    return tc1 * tc2 < 0 and td1 * td2 < 0

# point = (x,y)
# line1(point1)-(point2), line2(point3)-(point4)
# Calculate the angle made by two line segments - 線分同士が交差する角度を計算
def calcVectorAngle(point1, point2, point3, point4):
    u = np.array(line_vectorize(point1, point2))
    v = np.array(line_vectorize(point3, point4))
    i = np.inner(u, v)
    n = LA.norm(u) * LA.norm(v)
    c = i / n
    a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
    if u[0] * v[1] - u[1] * v[0] < 0:
        return a
    else:
        return 360 - a

# line(point1)-(point2)
# convert a line to a vector
def line_vectorize(point1, point2):
    a = point2[0] - point1[0]
    b = point2[1] - point1[1]
    return [a, b]