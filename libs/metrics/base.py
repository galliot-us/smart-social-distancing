import ast
import cv2 as cv
import os
import copy
import csv
import numpy as np
import pandas as pd
import logging
import numbers
from enum import Enum

from collections import deque
from datetime import date, datetime, timedelta, time
from typing import Dict, List, Iterator
from pandas.api.types import is_numeric_dtype

from libs.utils.config import get_source_config_directory
from libs.utils.loggers import get_source_log_directory, get_area_log_directory, get_source_logging_interval
from libs.utils.utils import is_list_recursively_empty, validate_file_exists_and_is_not_empty

logger = logging.getLogger(__name__)


class AggregationMode(Enum):
    SINGLE = 1
    BATCH = 2


def parse_date_range(dates):
    """Generator. From a continuous sorted list of datetime64 yields tuples (start_date, end_date) for each week encompassed"""
    while not dates.empty:
        start = 0
        end = (7 - dates[start].weekday()) - 1
        if end > len(dates):
            end = len(dates) - 1

        yield (dates[start], dates[end])
        dates = dates[end+1:]


class BaseMetric:
    processing_count_threshold = 3
    reports_folder = None
    csv_headers = []
    csv_default_values = []
    # entity value can be "source" or "area"
    entity = "source"
    # Use the `live_csv_headers` when the csv strucutre differs from the hourly/daily
    live_csv_headers = []
    # Values ignored when returning reports
    ignored_headers = []

    @classmethod
    def report_headers(cls):
        return [h for h in cls.csv_headers if h not in cls.ignored_headers]

    @classmethod
    def get_entity_base_directory(cls, config=None):
        if config:
            return get_source_log_directory(config) if cls.entity == "source" else get_area_log_directory(config)
        return os.getenv("SourceLogDirectory") if cls.entity == "source" else os.getenv("AreaLogDirectory")

    @classmethod
    def get_roi_file_path(cls, camera_id, config):
        """ Returns the path to the roi_contour file """
        return f"{get_source_config_directory(config)}/{camera_id}/roi_filtering/roi_contour.csv"

    @classmethod
    def get_roi_contour(cls, roi_file_path):
        """ Given the path to the roi file it loads it and returns it """
        if validate_file_exists_and_is_not_empty(roi_file_path):
            return np.loadtxt(roi_file_path, delimiter=',', dtype=int)
        else:
            return None

    @classmethod
    def get_roi_contour_for_entity(cls, config, source_id):
        if cls.entity == "area":
            return None
        return cls.get_roi_contour(cls.get_roi_file_path(source_id, config))

    @staticmethod
    def is_inside_roi(detected_object, roi_contour):
        """
        An object is inside the RoI if its middle bottom point lies inside it.
        params:
            detected_object: a dictionary, that has attributes of a detected object such as "id",
            "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box),
            "bbox" (a tuple of the normalized (xmin,ymin,xmax,ymax) coordinate of the box),
            "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and
            "bbox_real" (a tuple of the (xmin,ymin,xmax,ymax) coordinate of the box)

            roi_contour: An array of 2-tuples that compose the contour of the RoI
        returns:
        True of False: Depending if the objects coodinates are inside the RoI
        """
        corners = detected_object["bbox_real"]
        x1, x2 = int(corners[0]), int(corners[2])
        y1, y2 = int(corners[1]), int(corners[3])  # noqa
        if cv.pointPolygonTest(roi_contour, (x1 + (x2-x1)/2, y2), False) >= 0:
            return True
        return False

    @classmethod
    def ignore_objects_outside_roi(cls, csv_row, roi_contour):
        detections = ast.literal_eval(csv_row["Detections"])
        detections_in_roi = []
        for index, obj in enumerate(detections):
            obj["index"] = index
            if cls.is_inside_roi(obj, roi_contour):
                detections_in_roi.append(obj)
        violations_indexes = ast.literal_eval(csv_row["ViolationsIndexes"])
        violations_indexes_in_roi = []
        for index, obj in enumerate(detections_in_roi):
            if obj["index"] in violations_indexes:
                violations_indexes_in_roi.append(index)
        # Update the csv fields
        csv_row["Detections"] = str(detections_in_roi)
        csv_row["ViolationsIndexes"] = str(violations_indexes_in_roi)
        csv_row["DetectedObjects"] = len(detections_in_roi)
        csv_row["ViolatingObjects"] = len(violations_indexes_in_roi)
        return csv_row

    @classmethod
    def get_entities(cls, config):
        return config.get_video_sources() if cls.entity == "source" else config.get_areas()

    @classmethod
    def process_metric_csv_row(cls, csv_row, object_logs):
        """
        Extracts from the `csv_row` the required information to calculate the metric.
        The extracted information is populated into `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def process_csv_row(cls, csv_row, object_logs, roi_contour=None):
        if roi_contour is not None:
            csv_row = cls.ignore_objects_outside_roi(csv_row, roi_contour)
        cls.process_metric_csv_row(csv_row, object_logs)

    @classmethod
    def generate_hourly_metric_data(cls, config, object_logs, entity):
        """
        Generates the hourly reports for the hours received in `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def generate_hourly_csv_data(cls, config, entity: Dict, entity_file: str, time_from: datetime,
                                 time_until: datetime):
        roi_contour = cls.get_roi_contour_for_entity(config, entity["id"])
        if not os.path.isfile(entity_file):
            entity_type = "Camera" if cls.entity else "Area"
            logger.warn(f"The [{entity_type}: {entity['id']}] contains no recorded data for that day")
            return
        objects_logs = {}
        for hour in range(time_from.hour, time_until.hour):
            objects_logs[hour] = {}
        with open(entity_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row_time = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")
                if time_from <= row_time < time_until:
                    cls.process_csv_row(row, objects_logs, roi_contour)
            return cls.generate_hourly_metric_data(config, objects_logs, entity)

    @classmethod
    def compute_hourly_metrics(cls, config):
        if not cls.reports_folder:
            raise Exception(f"The metric {cls} doesn't have configured the folder parameter")
        entities = cls.get_entities(config)
        current_hour = datetime.now().hour
        for entity in entities:
            if not cls.can_execute(config, entity):
                continue
            entity_directory = entity.base_directory
            log_directory = None
            if cls.entity == "source":
                log_directory = os.path.join(entity_directory, "objects_log")
            else:
                # cls.entity == "area"
                log_directory = os.path.join(entity_directory, "occupancy_log")
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            # Create missing directories
            os.makedirs(log_directory, exist_ok=True)
            os.makedirs(reports_directory, exist_ok=True)
            time_until = datetime.combine(date.today(), time(current_hour, 0))
            report_date = cls.get_report_date()
            entity_csv = os.path.join(log_directory, str(report_date) + ".csv")
            daily_csv = os.path.join(reports_directory, "report_" + str(report_date) + ".csv")

            time_from = datetime.combine(report_date, time(0, 0))
            if os.path.isfile(daily_csv):
                with open(daily_csv, "r", newline='') as csvfile:
                    processed_hours = sum(1 for line in csv.reader(csvfile)) - 1
                    time_from = datetime.combine(report_date, time(processed_hours + 1, 0))
            else:
                with open(daily_csv, "a", newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=cls.csv_headers)
                    writer.writeheader()
            csv_data = cls.generate_hourly_csv_data(config, entity, entity_csv, time_from, time_until)
            if csv_data is None:
                entity_type = "Camera" if cls.entity else "Area"
                logger.warn(f"Hourly report not generated! [{entity_type}: {entity['id']}]")
                continue
            with open(daily_csv, "a", newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=cls.csv_headers)
                for item in csv_data:
                    row = {}
                    for index, header in enumerate(cls.csv_headers):
                        row[header] = item[index]
                    writer.writerow(row)

    @classmethod
    def generate_daily_csv_data(cls, yesterday_hourly_file):
        """
        Generates the daily report for the `yesterday_hourly_file` received.
        """
        raise NotImplementedError

    @classmethod
    def compute_daily_metrics(cls, config):
        base_directory = cls.get_entity_base_directory(config)
        entities = cls.get_entities(config)
        for entity in entities:
            if not cls.can_execute(config, entity):
                continue
            entity_directory = os.path.join(base_directory, entity["id"])
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            # Create missing directories
            os.makedirs(reports_directory, exist_ok=True)
            yesterday = str(date.today() - timedelta(days=1))
            hourly_csv = os.path.join(reports_directory, "report_" + yesterday + ".csv")
            report_csv = os.path.join(reports_directory, "report.csv")
            if not os.path.isfile(hourly_csv):
                entity_type = "Camera" if cls.entity else "Area"
                logger.warn(f"Daily report for date {str(yesterday)} not generated! [{entity_type}: {entity['id']}]")
                continue
            daily_data = cls.generate_daily_csv_data(hourly_csv)
            headers = ["Date"] + cls.csv_headers
            report_file_exists = os.path.isfile(report_csv)
            with open(report_csv, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)

                if not report_file_exists:
                    writer.writeheader()
                row = {"Date": yesterday}
                for index, header in enumerate(cls.csv_headers):
                    row[header] = daily_data[index]
                writer.writerow(row)

    @classmethod
    def generate_live_csv_data(cls, config, today_entity_csv, entity, entries_in_interval):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        raise NotImplementedError

    @classmethod
    def compute_live_metrics(cls, config, live_interval):
        base_directory = cls.get_entity_base_directory(config)
        entities = cls.get_entities(config)
        for entity in entities:
            if not cls.can_execute(config, entity):
                continue
            entity_directory = os.path.join(base_directory, entity["id"])
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            # Create missing directories
            os.makedirs(reports_directory, exist_ok=True)
            log_directory = None
            if cls.entity == "source":
                log_directory = os.path.join(entity_directory, "objects_log")
            else:
                # cls.entity == "area"
                log_directory = os.path.join(entity_directory, "occupancy_log")
            today_entity_csv = os.path.join(log_directory, str(date.today()) + ".csv")
            live_report_csv = os.path.join(reports_directory, "live.csv")
            csv_headers = cls.live_csv_headers if cls.live_csv_headers else cls.csv_headers
            headers = ["Time"] + csv_headers
            report_file_exists = os.path.isfile(live_report_csv)
            if not os.path.isfile(today_entity_csv):
                return
            entries_in_interval = int(live_interval * 60 / get_source_logging_interval(config))
            live_data = cls.generate_live_csv_data(config, today_entity_csv, entity, entries_in_interval)
            assert len(live_data) == len(csv_headers), "Row element count not the same as header count!!"
            with open(live_report_csv, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                if not report_file_exists:
                    writer.writeheader()
                row = {"Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                for index, header in enumerate(csv_headers):
                    row[header] = live_data[index]
                writer.writerow(row)

    @classmethod
    def get_hourly_report(cls, entities: List[str], report_date: date) -> Dict:
        base_directory = cls.get_entity_base_directory()
        hours = list(range(0, 24))
        results = {}
        hourly_headers = cls.report_headers()
        for index, header in enumerate(hourly_headers):
            if cls.csv_default_values[index] == 0:
                results[header] = np.zeros(24)
            else:
                results[header] = []
        for entity in entities:
            entity_directory = os.path.join(base_directory, entity)
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            file_path = os.path.join(reports_directory, f"report_{report_date}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                for header in hourly_headers:
                    if is_numeric_dtype(df[header]):
                        results[header] += np.pad(
                            df[header].to_numpy(), (0, 24 - df[header].to_numpy().size), mode="constant"
                        )
                    else:  # It's a list
                        values = df[header].apply(ast.literal_eval).tolist()
                        entry = np.pad(values, 0, mode="constant").tolist()
                        if is_list_recursively_empty(results[header]):
                            results[header] = entry
                        else:
                            results[header] = [[c + d for c, d in zip(a, b)] for a, b in zip(results[header], entry)]
        for metric in results:
            results[metric] = list(results[metric])
        results["Hours"] = hours
        return results

    @classmethod
    def get_daily_report(cls, entities: List[str], from_date: date, to_date: date) -> Dict:
        base_directory = cls.get_entity_base_directory()
        date_range = pd.date_range(start=from_date, end=to_date)
        base_results = {}
        daily_headers = cls.report_headers()
        for key in date_range:
            base_results[key.strftime('%Y-%m-%d')] = {}
            for index, header in enumerate(cls.csv_headers):
                base_results[key.strftime('%Y-%m-%d')][header] = copy.deepcopy(cls.csv_default_values[index])

        for entity in entities:
            entity_directory = os.path.join(base_directory, entity)
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            file_path = os.path.join(reports_directory, "report.csv")
            if not os.path.isfile(file_path):
                continue
            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
            mask = (df['Date'] >= pd.to_datetime(from_date)) & (df['Date'] <= pd.to_datetime(to_date))
            entity_report = df.loc[mask]
            entity_report['Date'] = entity_report['Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
            entity_report = entity_report.set_index('Date').T
            entity_report_dict = entity_report.to_dict()
            for key in entity_report_dict:
                for header in daily_headers:
                    if isinstance(entity_report_dict[key][header], numbers.Number):
                        base_results[key][header] += entity_report_dict[key][header]
                    else:  # It's a list
                        entry = ast.literal_eval(entity_report_dict[key][header])
                        if is_list_recursively_empty(base_results[key][header]):
                            base_results[key][header] = entry
                        else:
                            base_results[key][header] = [a + b for a, b in zip(base_results[key][header], entry)]

        report = {"Dates": []}
        for header in daily_headers:
            report[header] = []
        for report_date in sorted(base_results):
            report["Dates"].append(report_date)
            for header in daily_headers:
                report[header].append(base_results[report_date][header])
        return report

    @classmethod
    def generate_weekly_report_data(cls, entities: List[str], number_of_weeks: int = 0,
                                    from_date: date = None, to_date: date = None) -> Dict:
        weekly_report_data = {}
        number_of_days = number_of_weeks*7
        if number_of_days > 0:
            # Separate weeks in range taking a number of weeks ago, considering the week ended yesterday
            date_range = pd.date_range(end=date.today() - timedelta(days=1), periods=number_of_days)
            start_dates = date_range[0::7]
            end_dates = date_range[6::7]
            week_span = list(zip(start_dates, end_dates))
        elif isinstance(from_date, date) and isinstance(to_date, date):
            # Separate weeks in range considering the week starts on Monday
            date_range = pd.date_range(start=from_date, end=to_date)
            week_span = list(parse_date_range(date_range))
        else:
            week_span = []
        for start_date, end_date in week_span:
            weekly_report_data[
                f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
            ] = cls.get_daily_report(entities, start_date, end_date)
        return weekly_report_data

    @classmethod
    def get_weekly_report(cls, entities: List[str], number_of_weeks: int = 0,
                          from_date: date = None, to_date: date = None) -> Dict:
        weekly_report_data = cls.generate_weekly_report_data(entities, number_of_weeks, from_date, to_date)
        report = {"Weeks": []}
        weekly_headers = cls.report_headers()
        for header in weekly_headers:
            report[header] = []
        for week, week_data in weekly_report_data.items():
            report["Weeks"].append(week)
            for header in weekly_headers:
                report[header].append(sum(week_data[header]))
        return report

    @classmethod
    def get_trend_live_values(cls, live_report_paths: Iterator[str]) -> Iterator[int]:
        raise NotImplementedError

    @classmethod
    def calculate_trend_value(cls, trend_values: Iterator[int]) -> float:
        x = np.arange(0, len(trend_values))
        y = np.array(trend_values)
        z = np.polyfit(x, y, 1)
        return round(z[0], 2)

    @classmethod
    def get_live_report(cls, entities):
        base_directory = cls.get_entity_base_directory()
        report = {}
        live_headers = cls.live_csv_headers if cls.live_csv_headers else cls.csv_headers
        live_headers = [h for h in live_headers if h not in cls.ignored_headers]
        for index, header in enumerate(live_headers):
            report[header] = copy.deepcopy(cls.csv_default_values[index])
        times = []
        live_report_paths = []
        for entity in entities:
            entity_directory = os.path.join(base_directory, entity)
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            file_path = os.path.join(reports_directory, "live.csv")
            if not os.path.exists(file_path):
                continue
            live_report_paths.append(file_path)
            with open(file_path, "r") as live_file:
                lastest_entry = deque(csv.DictReader(live_file), 1)[0]
                times.append(datetime.strptime(lastest_entry["Time"], "%Y-%m-%d %H:%M:%S"))
                for header in live_headers:
                    if lastest_entry[header][0].isdigit():
                        report[header] += int(ast.literal_eval(lastest_entry[header]))
                    else:  # It's a list
                        entry = ast.literal_eval(lastest_entry[header])
                        if is_list_recursively_empty(report[header]):
                            report[header] = entry
                        else:
                            report[header] = [a + b for a, b in zip(report[header], entry)]
        report["Time"] = ""
        report["Trend"] = 0
        if times:
            report["Time"] = str(min(times))
        trend_live_values = cls.get_trend_live_values(live_report_paths)
        if trend_live_values:
            report["Trend"] = cls.calculate_trend_value(trend_live_values)
        return report

    @classmethod
    def can_execute(cls, config, entity):
        return True

    @classmethod
    def get_report_date(cls):
        if datetime.now().hour == 0:
            # Pending to process the latest hour from yesterday
            return date.today() - timedelta(days=1)
        else:
            return date.today()
