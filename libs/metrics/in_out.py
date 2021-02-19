import os
import ast
import json
import numpy as np
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
        # OrderedDict([('Version', '1.0'), ('Timestamp', '2021-02-19 15:28:49'), ('DetectedObjects', '3'), ('ViolatingObjects', '1'), ('EnvironmentScore', '0.95'), ('Detections', "[{'position': [0.0, 0.0, 0.0], 'bbox': [0.7269890795631825, 0.01084010840108401, 0.8065522620904836, 0.26287262872628725], 'tracking_id': 54, 'track_info': {'max_score': 0.9, 'lost': 0, 'score': 0.9, 'track_history': [(483, 44), (484, 46), (484, 48), (484, 50), (484, 51), (485, 52), (485, 52), (486, 53), (487, 53), (487, 55), (488, 55), (488, 53), (489, 53), (489, 54), (490, 55), (490, 57), (490, 58), (490, 61), (490, 64), (490, 65)]}, 'face_label': 0}, {'position': [0.0, 0.0, 0.0], 'bbox': [0.29797191887675506, 0.11924119241192412, 0.36349453978159124, 0.3604336043360434], 'tracking_id': 45, 'track_info': {'max_score': 0.9, 'lost': 0, 'score': 0.9, 'track_history': [(211, 115), (211, 116), (211, 115), (211, 115), (211, 116), (211, 116), (210, 115), (211, 115), (211, 115), (211, 115), (211, 115), (211, 115), (211, 115), (210, 115), (210, 115), (211, 114), (210, 114), (210, 114), (211, 113), (211, 115)]}}, {'position': [0.0, 0.0, 0.0], 'bbox': [0.6599063962558502, 0.018970189701897018, 0.717628705148206, 0.24932249322493225], 'tracking_id': 52, 'track_info': {'max_score': 0.9, 'lost': 0, 'score': 0.9, 'track_history': [(446, 89), (445, 86), (445, 85), (445, 84), (445, 84), (444, 82), (443, 81), (444, 81), (444, 81), (442, 84), (442, 77), (442, 73), (440, 71), (440, 70), (442, 68), (441, 68), (440, 67), (440, 66), (440, 64), (440, 64)]}}]"), ('ViolationsIndexes', '[0, 2]')])
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
        raise NotImplementedError("Operation not implemented")

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

# Multiple lines cross check
def checkLineCrosses(boundaryLines, objects):
    for obj in objects:
        traj = obj.trajectory
        if len(traj) > 1:
            p0 = traj[-2]
            p1 = traj[-1]
            for line in boundaryLines:
                checkLineCross(line, [p0[0], p0[1], p1[0], p1[1]])

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