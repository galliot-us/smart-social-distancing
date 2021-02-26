import os
import csv
import numpy as np
import pandas as pd
import logging

from collections import deque
from datetime import date, datetime, timedelta, time
from typing import Dict, List, Iterator

from libs.utils.loggers import get_source_log_directory, get_area_log_directory, get_source_logging_interval

logger = logging.getLogger(__name__)


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
    metric_name = None
    processing_count_threshold = 3
    reports_folder = None
    csv_headers = []
    # entity value can be "source" or "area"
    entity = "source"
    # Use the `live_csv_headers` when the csv strucutre differs from the hourly/daily
    live_csv_headers = []

    @classmethod
    def get_entity_base_directory(cls, config=None):
        if config:
            return get_source_log_directory(config) if cls.entity == "source" else get_area_log_directory(config)
        return os.getenv("SourceLogDirectory") if cls.entity == "source" else os.getenv("AreaLogDirectory")

    @classmethod
    def get_entities(cls, config):
        return config.get_video_sources() if cls.entity == "source" else config.get_areas()

    @classmethod
    def process_csv_row(cls, csv_row, object_logs):
        """
        Extracts from the `csv_row` the required information to calculate the metric.
        The extracted information is populated into `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def generate_hourly_metric_data(cls, object_logs, entity):
        """
        Generates the hourly reports for the hours received in `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def generate_hourly_csv_data(cls, entity: Dict, entity_file: str, time_from: datetime,
                                 time_until: datetime):
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
                    cls.process_csv_row(row, objects_logs)
            return cls.generate_hourly_metric_data(objects_logs, entity)

    @classmethod
    def compute_hourly_metrics(cls, config):
        if not cls.reports_folder:
            raise Exception(f"The metric {cls} doesn't have configured the folder parameter")
        base_directory = cls.get_entity_base_directory(config)
        entities = cls.get_entities(config)
        current_hour = datetime.now().hour
        for entity in entities:
            entity_directory = os.path.join(base_directory, entity["id"])
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
            if current_hour == 0:
                # Pending to process the latest hour from yesterday
                report_date = date.today() - timedelta(days=1)
            else:
                report_date = date.today()
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
            csv_data = cls.generate_hourly_csv_data(entity, entity_csv, time_from, time_until)
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
            entity["base_directory"] = entity_directory
            entries_in_interval = int(live_interval * 60 / get_source_logging_interval(config))
            if not cls.can_execute(config, entity):
                return
            live_data = cls.generate_live_csv_data(config, today_entity_csv, entity, entries_in_interval)
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
        for header in cls.csv_headers:
            results[header] = np.zeros(24)
        for entity in entities:
            entity_directory = os.path.join(base_directory, entity)
            reports_directory = os.path.join(entity_directory, "reports", cls.reports_folder)
            file_path = os.path.join(reports_directory, f"report_{report_date}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                for header in cls.csv_headers:
                    results[header] += np.pad(
                        df[header].to_numpy(), (0, 24 - df[header].to_numpy().size), mode="constant"
                    )
        for metric in results:
            results[metric] = results[metric].tolist()
        results["Hours"] = hours
        return results

    @classmethod
    def get_daily_report(cls, entities: List[str], from_date: date, to_date: date) -> Dict:
        base_directory = cls.get_entity_base_directory()
        date_range = pd.date_range(start=from_date, end=to_date)
        base_results = {}
        for key in date_range:
            base_results[key.strftime('%Y-%m-%d')] = {}
            for header in cls.csv_headers:
                base_results[key.strftime('%Y-%m-%d')][header] = 0

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
                for header in cls.csv_headers:
                    base_results[key][header] += entity_report_dict[key][header]

        report = {"Dates": []}
        for header in cls.csv_headers:
            report[header] = []
        for report_date in sorted(base_results):
            report["Dates"].append(report_date)
            for header in cls.csv_headers:
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
        for header in cls.csv_headers:
            report[header] = []
        for week, week_data in weekly_report_data.items():
            report["Weeks"].append(week)
            for header in cls.csv_headers:
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
        for header in live_headers:
            report[header] = 0
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
                    report[header] += int(lastest_entry[header])
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
        return False
