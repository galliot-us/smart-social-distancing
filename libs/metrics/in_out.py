import ast
import csv
import json
import os
import numpy as np
import copy

from collections import deque
from datetime import date
from typing import Dict, Iterator, List
from datetime import datetime
from statistics import mean

from .base import BaseMetric
from constants import IN_OUT
from libs.utils.config import get_source_config_directory
from libs.utils.utils import validate_file_exists_and_is_not_empty, is_list_recursively_empty
from libs.utils.in_out import check_line_cross


class InOutMetric(BaseMetric):

    reports_folder = IN_OUT
    csv_headers = ["In", "Out", "EstimatedMaxOccupancy", "EstimatedAverageOccupancy", "EstimatedLatestOccupancy", "Summary"]
    csv_default_values = [0, 0, 0, 0, 0, [[], [], []]]
    NUMBER_OF_PATH_SEGMENTS = 7
    SEGMENTATION_MINUTES = 10

    @classmethod
    def process_metric_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour, row_minute = row_time.hour, row_time.minute
        intervals_per_hour = 60 // cls.SEGMENTATION_MINUTES
        segment = row_minute // cls.SEGMENTATION_MINUTES
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {key: {} for key in range(intervals_per_hour)}
        for d in detections:
            if not objects_logs[row_hour][segment].get(d["tracking_id"]):
                objects_logs[row_hour][segment][d["tracking_id"]] = {"path": []}
            # Append bottom middle positions
            corners = d["bbox_real"]
            x1, x2 = int(corners[0]), int(corners[2])
            _, y2 = int(corners[1]), int(corners[3])
            bottom_middle_position = (x1 + (x2 - x1) / 2, y2)
            objects_logs[row_hour][segment][d["tracking_id"]]["path"].append(bottom_middle_position)

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        people_in, people_out = 0, 0
        estimated_max_occupancy, estimated_average_occupancy, boundary_names = [], [], []
        estimated_latest_occupancy = _read_estimated_latest_occupancy(yesterday_hourly_file)
        with open(yesterday_hourly_file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                people_in += int(row["In"])
                people_out += int(row["Out"])
                estimated_max_occupancy.append(int(row["EstimatedMaxOccupancy"]))
                estimated_average_occupancy.append(float(row["EstimatedAverageOccupancy"]))

                if not is_list_recursively_empty(row["Summary"]):
                    hourly_boundary_names, hourly_in, hourly_out = ast.literal_eval(row["Summary"])
                    hourly_in, hourly_out = np.array(hourly_in, dtype=int), np.array(hourly_out, dtype=int)
                    if not boundary_names:
                        boundary_names = hourly_boundary_names
                        daily_in = np.zeros(len(boundary_names), dtype=int)
                        daily_out = np.zeros(len(boundary_names), dtype=int)
                    daily_in += hourly_in
                    daily_out += hourly_out
        estimated_max_occupancy = max(estimated_max_occupancy)
        estimated_average_occupancy = round(mean(estimated_average_occupancy), 2)
        summary = [boundary_names, list(daily_in), list(daily_out)]
        return people_in, people_out, estimated_max_occupancy, estimated_average_occupancy, estimated_latest_occupancy, summary

    @classmethod
    def generate_hourly_metric_data(cls, config, objects_logs, entity):
        boundaries = cls.retrieve_in_out_boundaries(config, entity["id"])
        boundary_names = [boundary["name"] for boundary in boundaries]
        hourly_summary = [0, 0, 0, 0, 0, [boundary_names, [0] * len(boundaries), [0] * len(boundaries)]]
        summary = [copy.deepcopy(hourly_summary) for x in range(len(objects_logs))]
        reports_directory = os.path.join(entity.base_directory, "reports", cls.reports_folder)
        daily_csv = os.path.join(reports_directory, "report_" + str(cls.get_report_date()) + ".csv")
        latest_estimated_occupancy = _read_estimated_latest_occupancy(daily_csv)

        for index_hour, hour in enumerate(sorted(objects_logs)):
            hour_in, hour_out, hour_balance = [], [], []
            cls._process_hourly_segments(
                objects_logs[hour], latest_estimated_occupancy, boundaries,
                hour_in, hour_out, hour_balance, summary[index_hour][5]
            )
            if not hour_balance:
                hour_balance = [0]
            summary[index_hour][0] = sum(hour_in)
            summary[index_hour][1] = sum(hour_out)
            summary[index_hour][2] = max(0, max(hour_balance))  # estimated_max_occupancy
            summary[index_hour][3] = max(0, round(mean(hour_balance), 2))  # estimated_average_occupancy
            summary[index_hour][4] = max(0, hour_balance[-1])  # estimated_latest_occupancy
        return summary

    @classmethod
    def generate_live_csv_data(cls, config, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        boundaries = cls.retrieve_in_out_boundaries(config, entity["id"])
        boundary_names = [boundary["name"] for boundary in boundaries]
        roi_contour = cls.get_roi_contour_for_entity(config, entity["id"])

        live_csv = os.path.join(entity.base_directory, "reports", cls.reports_folder, "live.csv")
        latest_estimated_occupancy = _read_estimated_latest_occupancy(live_csv)
        summary = [0, 0, 0, 0, 0, [boundary_names, [0] * len(boundaries), [0] * len(boundaries)]]
        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            lastest_entries = deque(csv.DictReader(log), entries_in_interval)
            for entry in lastest_entries:
                cls.process_csv_row(entry, objects_logs, roi_contour)

        hour_in, hour_out, hour_balance = [], [], []
        for hour in sorted(objects_logs):
            cls._process_hourly_segments(
                objects_logs[hour], latest_estimated_occupancy, boundaries,
                hour_in, hour_out, hour_balance, summary[5]
            )
        summary[0] = sum(hour_in)
        summary[1] = sum(hour_out)
        summary[2] = max(0, max(hour_balance))  # estimated_max_occupancy
        summary[3] = max(0, round(mean(hour_balance), 2))  # estimated_average_occupancy
        summary[4] = max(0, hour_balance[-1])  # estimated_latest_occupancy
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
        report = {
            "Weeks": [],
            "InMax": [],
            "OutMax": [],
            "InAvg": [],
            "OutAvg": [],
        }
        for header in cls.csv_headers:
            report[header] = []
        for week, week_data in weekly_report_data.items():
            estimated_max_occ = max(week_data["EstimatedMaxOccupancy"]) if week_data["EstimatedMaxOccupancy"] else 0
            estimated_avg_occ = round(mean(week_data["EstimatedAverageOccupancy"]), 2) if week_data["EstimatedAverageOccupancy"] else 0
            estimated_latest_occ = round(week_data["EstimatedLatestOccupancy"][-1]) if week_data["EstimatedLatestOccupancy"] else 0
            in_sum = sum(week_data["In"])
            out_sum = sum(week_data["Out"])
            in_max = max(week_data["In"]) if week_data["In"] else 0
            out_max = max(week_data["Out"]) if week_data["Out"] else 0
            in_avg = round(mean(week_data["In"]), 2) if week_data["In"] else 0
            out_avg = round(mean(week_data["Out"]), 2) if week_data["Out"] else 0
            report["Weeks"].append(week)
            report["In"].append(in_sum)
            report["Out"].append(out_sum)
            report["InMax"].append(in_max)
            report["OutMax"].append(out_max)
            report["InAvg"].append(in_avg)
            report["OutAvg"].append(out_avg)
            report["EstimatedMaxOccupancy"].append(estimated_max_occ)
            report["EstimatedAverageOccupancy"].append(estimated_avg_occ)
            report["EstimatedLatestOccupancy"].append(estimated_latest_occ)
            if is_list_recursively_empty(week_data["Summary"]):
                boundary_name = []
                weekly_in = []
                weekly_out = []
            else:
                boundary_names, weekly_in, weekly_out = list(zip(*week_data["Summary"]))
                boundary_name = next(x for x in boundary_names if not is_list_recursively_empty(x))
                weekly_in = _fill_partially_empty_result(weekly_in, 0)
                weekly_out = _fill_partially_empty_result(weekly_out, 0)

            report["Summary"].append([
                boundary_name,
                [sum(x) for x in zip(*weekly_in)],
                [sum(x) for x in zip(*weekly_out)]
            ])
        return report

    @classmethod
    def _process_path(cls, boundary_line, trajectory_path, number_of_cuts=NUMBER_OF_PATH_SEGMENTS):
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
    def _process_hourly_segments(
        cls, hourly_objects_logs, latest_estimated_occupancy, boundaries,  # input
        hour_in, hour_out, hour_balance, summary_report  # output
    ):
        for index_segment, segment in enumerate(hourly_objects_logs):
            segment_objects_detections = hourly_objects_logs[segment]
            segment_in, segment_out = 0, 0
            for track_id, data in segment_objects_detections.items():
                path = data["path"]
                for index_boundary, boundary in enumerate(boundaries):
                    boundary_line = boundary["in_out_boundary"]
                    new_in, new_out = cls._process_path(boundary_line, path)
                    segment_in += new_in
                    segment_out += new_out
                    summary_report[1][index_boundary] += new_in
                    summary_report[2][index_boundary] += new_out
            latest_estimated_occupancy += (segment_in - segment_out)
            hour_in.append(segment_in)
            hour_out.append(segment_out)
            hour_balance.append(latest_estimated_occupancy)


def _fill_partially_empty_result(tuple_of_lists, default_value):
    tuple_of_lists = list(tuple_of_lists)
    length_of_sublists = len(next(x for x in tuple_of_lists if not is_list_recursively_empty(x)))
    for i in range(len(tuple_of_lists)):
        if is_list_recursively_empty(tuple_of_lists[i]):
            tuple_of_lists[i] = [default_value] * length_of_sublists
    return tuple_of_lists


def _read_estimated_latest_occupancy(in_out_file_path):
    def _is_today(entry):
        return datetime.strptime(entry["Time"], "%Y-%m-%d %H:%M:%S").date() == datetime.today().date()
    if os.path.exists(in_out_file_path):
        with open(in_out_file_path, "r") as in_out_file:
            latest_entry = deque(csv.DictReader(in_out_file), 1)
            if len(latest_entry) != 0 and ("Time" not in latest_entry[0] or _is_today(latest_entry[0])):
                return int(latest_entry[0]["EstimatedLatestOccupancy"])
    return 0
