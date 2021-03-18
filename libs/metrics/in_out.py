import ast
import csv
import json
import numpy as np

from numpy import linalg as LA
from collections import deque
from datetime import date
from typing import Dict, Iterator, List
from datetime import datetime

from .base import BaseMetric
from constants import IN_OUT
from libs.utils.config import get_source_config_directory
from libs.utils.utils import validate_file_exists_and_is_not_empty, is_list_recursively_empty


class InOutMetric(BaseMetric):

    reports_folder = IN_OUT
    csv_headers = ["In", "Out", "Summary"]
    csv_default_values = [0, 0, [[], [], []]]
    NUMBER_OF_PATH_SEGMENTS = 7

    @classmethod
    def process_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        for d in detections:
            if not objects_logs[row_hour].get(d["tracking_id"]):
                objects_logs[row_hour][d["tracking_id"]] = {"path": []}
            # Append bottom middle positions
            corners = d["bbox_real"]
            x1, x2 = int(corners[0]), int(corners[2])
            y1, y2 = int(corners[1]), int(corners[3])
            bottom_middle_position = (x1 + (x2 - x1) / 2, y2)
            objects_logs[row_hour][d["tracking_id"]]["path"].append(bottom_middle_position)

    @classmethod
    def process_path(cls, boundary_line, trajectory_path, number_of_cuts=NUMBER_OF_PATH_SEGMENTS):
        """
        Verify if a trajectory goes over a boundary line
        Args:
            Two coordinates [x,y] are in 2-tuples [A,B]
                Boundaries of the in/out line.
                If someone crosses the line while having A to their right, they are going in the in direction (entering)
                Crossing the line while having A to their left means they are going in the out direction (leaving)

            trajectory_path: List of N 2-tuples (x,y)
            That represents the trajectory of an object.

        Returns:
            (in, out) : tuple
                 (1, 1) - if the object entered and left an equal number of times.
                 (1, 0) - if the object entered (in)
                 (0, 1) - if the object left (out)
                 (0, 0) - if the object didn't cross the boundary.
        """
        if len(trajectory_path) < number_of_cuts:
            number_of_cuts = len(trajectory_path)

        trajectory_steps = [trajectory_path[int(i)] for i in np.linspace(0, len(trajectory_path) - 1, number_of_cuts)]
        trajectory_steps = zip(trajectory_steps, trajectory_steps[1:])
        total_in, total_out = 0, 0

        for trajectory in trajectory_steps:
            path_in, path_out = check_line_cross(boundary_line, trajectory)
            total_in += path_in
            total_out += path_out

        # Normalize in_out:
        return (int(total_in >= total_out and total_in > 0), int(total_out >= total_in and total_out > 0))

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        people_in, people_out = 0, 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                people_in += int(row["In"])
                people_out += int(row["Out"])
        return people_in, people_out

    @classmethod
    def generate_hourly_metric_data(cls, config, objects_logs, entity):
        boundaries = cls.retrieve_in_out_boundaries(config, entity["id"])
        boundary_names = [boundary["name"] for boundary in boundaries]
        summary = [[0, 0, [boundary_names, [0]*len(boundaries), [0]*len(boundaries)]]]*len(objects_logs)
        for index_hour, hour in enumerate(sorted(objects_logs)):
            hour_objects_detections = objects_logs[hour]
            for track_id, data in hour_objects_detections.items():
                path = data["path"]
                for index_boundary, boundary in enumerate(boundaries):
                    boundary_line = boundary["in_out_boundary"]
                    new_in, new_out = cls.process_path(boundary_line, path)
                    summary[index_hour][0] += new_in
                    summary[index_hour][1] += new_out
                    summary[index_hour][2][1][index_boundary] += new_in
                    summary[index_hour][2][2][index_boundary] += new_out
        return summary

    @classmethod
    def generate_live_csv_data(cls, config, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        boundaries = cls.retrieve_in_out_boundaries(config, entity["id"])
        boundary_names = [boundary["name"] for boundary in boundaries]
        summary = [0, 0, [boundary_names, [0] * len(boundaries), [0] * len(boundaries)]]
        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            lastest_entries = deque(csv.DictReader(log), entries_in_interval)
            for entry in lastest_entries:
                cls.process_csv_row(entry, objects_logs)
        paths = {}
        for hour in objects_logs:
            for track_id, sub_path in objects_logs[hour].items():
                if track_id not in paths:
                    paths[track_id] = sub_path
                else:
                    paths[track_id].extend(sub_path)
        for track_id, data in paths.items():
            path = data["path"]
            for index_boundary, boundary in enumerate(boundaries):
                boundary_line = boundary["in_out_boundary"]
                new_in, new_out = cls.process_path(boundary_line, path)
                summary[0] += new_in
                summary[1] += new_out
                summary[2][1][index_boundary] += new_in
                summary[2][2][index_boundary] += new_out
        return summary

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        latest_in_out_results = {}
        for n in range(10):
            latest_in_out_results[n] = None
        for live_path in live_report_paths:
            with open(live_path, "r") as live_file:
                lastest_10_entries = deque(csv.DictReader(live_file), 10)
                for index, item in enumerate(lastest_10_entries):
                    if not latest_in_out_results[index]:
                        latest_in_out_results[index] = 0
                    latest_in_out_results[index] += int(item["In"]) + int(item["Out"])
        return [item for item in latest_in_out_results.values() if item is not None]

    @classmethod
    def get_in_out_file_path(cls, camera_id, config):
        """ Returns the path to the roi_contour file """
        return f"{get_source_config_directory(config)}/{camera_id}/{IN_OUT}/{IN_OUT}.json"

    @classmethod
    def retrieve_in_out_boundaries(cls, config, camera_id):
        boundary_path = cls.get_in_out_file_path(camera_id, config)
        boundary_line = cls.read_in_out_boundaries(boundary_path)
        if boundary_line is None:
            raise Exception(f"Camera {camera_id} does not have a defined in/out boundary")
        else:
            return boundary_line["in_out_boundaries"]

    @classmethod
    def read_in_out_boundaries(cls, in_out_file_path):
        """ Given the path to the in-out file it loads it and returns it """
        if validate_file_exists_and_is_not_empty(in_out_file_path):
            with open(in_out_file_path) as json_file:
                in_out_boundaries = json.load(json_file)
            return in_out_boundaries
        else:
            return None

    @classmethod
    def can_execute(cls, config, entity):
        boundary_line = cls.read_in_out_boundaries(cls.get_in_out_file_path(entity["id"], config))
        if boundary_line is None:
            return False
        return True


    @classmethod
    def get_weekly_report(cls, entities: List[str], number_of_weeks: int = 0,
                          from_date: date = None, to_date: date = None) -> Dict:
        # The In/Out metric cannot be fully aggregated using "sum"
        weekly_report_data = cls.generate_weekly_report_data(entities, number_of_weeks, from_date, to_date)
        report = { "Weeks": [] }
        for header in cls.csv_headers:
            report[header] = []
        for week, week_data in weekly_report_data.items():
            report["Weeks"].append(week)
            report["In"].append(sum(week_data["In"]))
            report["Out"].append(sum(week_data["Out"]))
            if is_list_recursively_empty(week_data["Summary"]):
                boundary_name = []
                weekly_in = []
                weekly_out = []
            else:
                boundary_names, weekly_in, weekly_out = list(zip(*week_data["Summary"]))
                boundary_name = next(x for x in boundary_names if not is_list_recursively_empty(x))
                weekly_in = fill_partially_empty_result(weekly_in, 0)
                weekly_out = fill_partially_empty_result(weekly_out, 0)

            report["Summary"].append([
                boundary_name,
                [sum(x) for x in zip(*weekly_in)],
                [sum(x) for x in zip(*weekly_out)]
            ])
        return report

def fill_partially_empty_result(tuple_of_lists, default_value):
    tuple_of_lists = list(tuple_of_lists)
    length_of_sublists = len(next(x for x in tuple_of_lists if not is_list_recursively_empty(x)))
    for i in range(len(tuple_of_lists)):
        if is_list_recursively_empty(tuple_of_lists[i]):
            tuple_of_lists[i] = [default_value] * length_of_sublists
    return tuple_of_lists

# Auxiliary methods taken from:
# https://github.com/yas-sim/object-tracking-line-crossing-area-intrusion/blob/master/object-detection-and-line-cross.py
def check_line_cross(boundary_line, trajectory):
    """
    Args:
        boundary_line: Two coordinates [x,y] are in 2-tuples [A,B]
                Boundaries of the in/out line.
                If someone crosses the line while having A to their right, they are going in the in direction (entering)
                Crossing the line while having A to their left means they are going in the out direction (leaving)
        trajectory: vector ((x1, y1), (x2, y2))

    Returns:
        (in, out) : tuple
             (1, 0) - if the trajectory crossed the boundary entering (in)
             (0, 1) - if the trajectory crossed the boundary leaving (out)
             (0, 0) - if the trajectory didn't cross the boundary.
    """
    traj_p0 = (trajectory[0][0], trajectory[0][1])  # Trajectory of an object
    traj_p1 = (trajectory[1][0], trajectory[1][1])
    b_line_p0 = (boundary_line[0][0], boundary_line[0][1])  # Boundary line
    b_line_p1 = (boundary_line[1][0], boundary_line[1][1])
    intersect = check_intersect(traj_p0, traj_p1, b_line_p0, b_line_p1)  # Check if intersect or not
    if intersect == False:
        return 0, 0

    angle = calc_vector_angle(traj_p0, traj_p1, b_line_p0, b_line_p1)  # Calculate angle between trajectory and boundary line
    if angle < 180: # in
        return 1, 0
    else: # out
        return 0, 1

def check_intersect(p1, p2, p3, p4):
    """
    Check if the line p1-p2 intersects the line p3-p4
    Args:
        p1: (x,y)
        p2: (x,y)
        p3: (x,y)
        p4: (x,y)

    Returns:
        boolean : True if intersection occurred
    """
    tc1 = (p1[0] - p2[0]) * (p3[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p3[0])
    tc2 = (p1[0] - p2[0]) * (p4[1] - p1[1]) + (p1[1] - p2[1]) * (p1[0] - p4[0])
    td1 = (p3[0] - p4[0]) * (p1[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p1[0])
    td2 = (p3[0] - p4[0]) * (p2[1] - p3[1]) + (p3[1] - p4[1]) * (p3[0] - p2[0])
    return tc1 * tc2 < 0 and td1 * td2 < 0

def calc_vector_angle(line1_p1, line1_p2, line2_p1, line2_p2):
    """
    Calculate the and return the angle made by two line segments line1(p1)-(p2), line2(p1)-(p2)
    Args:
        line1_p1: (x,y)
        line1_p2: (x,y)
        line2_p1: (x,y)
        line2_p2: (x,y)

    Returns:
        angle : [0, 360)
    """
    u = np.array(line_vectorize(line1_p1, line1_p2))
    v = np.array(line_vectorize(line2_p1, line2_p2))
    i = np.inner(u, v)
    n = LA.norm(u) * LA.norm(v)
    c = i / n
    a = np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))
    if u[0] * v[1] - u[1] * v[0] < 0:
        return a
    else:
        return 360 - a

def line_vectorize(point1, point2):
    """
    Args:
        point1: (x,y)
        point2: (x,y)

    Returns:
        The vector of intersecting the points with a line line(point1)-(point2)
    """
    a = point2[0] - point1[0]
    b = point2[1] - point1[1]
    return [a, b]
