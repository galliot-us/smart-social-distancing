import csv
import ast
import numpy as np
import os
from statistics import mean

from collections import deque
from datetime import datetime, date
from typing import Dict, List, Iterator, Tuple

from .base import BaseMetric, AggregationMode
from constants import DWELL_TIME

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class DwellTimeMetric(BaseMetric):

    reports_folder = DWELL_TIME
    csv_headers = ["DetectedObjects", "L1", "L2", "L3", "L4", "L5", "AvgDwellTime", "MaxDwellTime", "Active"]
    ignored_headers = ["Active"]
    csv_default_values = [0, 0, 0, 0, 0, 0, 0, 0, "{}"]
    aggregation_mode = AggregationMode.SINGLE
    L1_THRESHOLD = 10
    L2_THRESHOLD = 30
    L3_THRESHOLD = 60
    L4_THRESHOLD = 180
    L5_THRESHOLD = 300
    ACTIVE_TRACK_INTERVAL = 10

    @classmethod
    def process_metric_csv_row(cls, csv_row: Dict, objects_logs: Dict):
        row_time = datetime.strptime(csv_row["Timestamp"], "%Y-%m-%d %H:%M:%S")
        detections = ast.literal_eval(csv_row["Detections"])
        row_hour = row_time.hour
        if not objects_logs.get(row_hour):
            objects_logs[row_hour] = {}
        for index, d in enumerate(detections):
            if not objects_logs[row_hour].get(d["tracking_id"]):
                objects_logs[row_hour][d["tracking_id"]] = {"times": []}
            objects_logs[row_hour][d["tracking_id"]]["times"].append(
                {
                    "time": row_time
                }
            )
        objects_logs[row_hour]["latest_time"] = row_time

    @classmethod
    def generate_hourly_metric_data(cls, config, objects_logs, entity=None):
        reports_directory = os.path.join(entity.base_directory, "reports", cls.reports_folder)
        daily_csv = os.path.join(reports_directory, "report_" + str(cls.get_report_date()) + ".csv")
        latest_active_ids = _read_estimated_latest_active_ids(daily_csv)
        return cls.calculate_metrics(objects_logs, latest_active_ids)

    @classmethod
    def calculate_metrics(cls, objects_logs, latest_active_ids):
        summary = np.zeros((len(objects_logs), 6), dtype=np.long)
        result = []
        for index, hour in enumerate(sorted(objects_logs)):
            hour_objects_detections = objects_logs[hour]
            if "latest_time" not in hour_objects_detections:
                result.append(cls.csv_default_values)
                continue
            latest_time = objects_logs[hour]["latest_time"]
            max_s = 0
            total_s = 0
            active_after_hour = {}
            previous_active_counted = set()
            for track_id, detection_object in hour_objects_detections.items():
                if track_id == "latest_time":
                    continue
                times = detection_object["times"]
                if track_id in latest_active_ids:
                    start = datetime.strptime(latest_active_ids[track_id]["start"], DATE_FORMAT)
                    previous_active_counted.add(track_id)
                else:
                    start = times[0]["time"]
                end = times[-1]["time"]
                dwell_seconds = (end - start).seconds
                if dwell_seconds < 3:
                    # You don't count. You are invisible to us
                    continue
                # If the detection was seen in the last ACTIVE_TRACK_INTERVAL seconds then
                # we don't count it and only count it during the next hour
                if (latest_time - end).seconds < cls.ACTIVE_TRACK_INTERVAL:
                    active_after_hour[track_id] = {"start": start.strftime(DATE_FORMAT), "time": dwell_seconds}
                    continue

                if dwell_seconds > max_s:
                    max_s = dwell_seconds
                total_s += dwell_seconds
                summary[index] += cls.get_level_result(dwell_seconds)

            # Count missing from previous hour
            for track_id in latest_active_ids.keys():
                if track_id not in previous_active_counted:
                    dwell_seconds = latest_active_ids[track_id]["time"]
                    if dwell_seconds > max_s:
                        max_s = dwell_seconds
                    total_s += dwell_seconds
                    summary[index] += cls.get_level_result(dwell_seconds)

            hour_result = list(summary[index])
            # Avg
            if summary[index][0] == 0:
                hour_result.append(0)
            else:
                hour_result.append(round(total_s / summary[index][0], 2))
            # Max
            hour_result.append(max_s)
            # Active
            hour_result.append(active_after_hour)
            result.append(hour_result)

            latest_active_ids = active_after_hour

        return result

    @classmethod
    def get_level_result(cls, dwell_seconds: int) -> Tuple[int, int, int, int, int, int]:
        if dwell_seconds > cls.L5_THRESHOLD:
            return 1, 0, 0, 0, 0, 1
        elif dwell_seconds > cls.L4_THRESHOLD:
            return 1, 0, 0, 0, 1, 0
        elif dwell_seconds > cls.L3_THRESHOLD:
            return 1, 0, 0, 1, 0, 0
        elif dwell_seconds > cls.L2_THRESHOLD:
            return 1, 0, 1, 0, 0, 0
        elif dwell_seconds > cls.L1_THRESHOLD:
            return 1, 1, 0, 0, 0, 0
        else:
            return 1, 0, 0, 0, 0, 0

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        detected_objects, l1, l2, l3, l4, l5 = 0, 0, 0, 0, 0, 0
        with open(yesterday_hourly_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            avg = []
            max_d = 0
            for row in reader:
                detected_objects += int(row["DetectedObjects"])
                l1 += int(row["L1"])
                l2 += int(row["L2"])
                l3 += int(row["L3"])
                l4 += int(row["L4"])
                l5 += int(row["L5"])
                avg.append(float(row["AvgDwellTime"]))
                max_d = max(max_d, int(row["MaxDwellTime"]))
        return detected_objects, l1, l2, l3, l4, l5, round(mean(avg), 2), max_d, "{}"

    @classmethod
    def generate_live_csv_data(cls, config, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        roi_contour = cls.get_roi_contour_for_entity(config, entity["id"])
        live_csv = os.path.join(entity.base_directory, "reports", cls.reports_folder, "live.csv")
        latest_active_ids = _read_estimated_latest_active_ids(live_csv)
        with open(today_entity_csv, "r") as log:
            objects_logs = {}
            lastest_entries = deque(csv.DictReader(log), entries_in_interval)
            for entry in lastest_entries:
                cls.process_csv_row(entry, objects_logs, roi_contour)
        metric_data = cls.calculate_metrics(objects_logs, latest_active_ids)
        numerics = np.zeros(6, dtype=np.long)
        avg = 0.
        total = 0
        max_l = 0
        for h in metric_data:
            numerics += h[:6]
            avg += h[0] * h[6]
            total += h[0]
            max_l = max(max_l, h[7])
        avg = avg / total
        result = list(numerics)
        result.extend([avg, max_l, metric_data[-1][8]])
        return result

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        latest_dwell_time_results = {}
        for n in range(10):
            latest_dwell_time_results[n] = None
        for live_path in live_report_paths:
            with open(live_path, "r") as live_file:
                lastest_10_entries = deque(csv.DictReader(live_file), 10)
                for index, item in enumerate(lastest_10_entries):
                    if not latest_dwell_time_results[index]:
                        latest_dwell_time_results[index] = 0.0
                    latest_dwell_time_results[index] += float(item["AvgDwellTime"])
        return [item for item in latest_dwell_time_results.values() if item is not None]

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
            report["AvgDwellTime"].append(round(mean(week_data["AvgDwellTime"]), 2))
            report["MaxDwellTime"].append(max(week_data["MaxDwellTime"]))
            for header in ["DetectedObjects", "L1", "L2", "L3", "L4", "L5"]:
                report[header].append(sum(week_data[header]))
        return report


def _read_estimated_latest_active_ids(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as dwell_file:
            latest_entry = deque(csv.DictReader(dwell_file), 1)
            if len(latest_entry) != 0 and latest_entry[0]["Active"] != "":
                return ast.literal_eval(latest_entry[0]["Active"])
    return {}
