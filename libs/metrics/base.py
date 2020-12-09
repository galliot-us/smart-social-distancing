import os
import csv
import logging

from datetime import date, datetime, timedelta, time
from libs.utils.loggers import get_source_log_directory, get_area_log_directory

logger = logging.getLogger(__name__)


class BaseMetric:
    processing_count_threshold = 3
    reports_folder = None
    csv_headers = []
    # entity value can be "source" or "area"
    entity = "source"

    @classmethod
    def procces_csv_row(cls, csv_row, object_logs):
        """
        Extracts from the `csv_row` the required information to calculate the metric.
        The extracted information is populated into `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def generate_hourly_metric_data(cls, object_logs):
        """
        Generates the hourly reports for the hours received in `object_logs`.
        """
        raise NotImplementedError

    @classmethod
    def generate_hourly_csv_data(cls, entity_id: str, entity_file: str, time_from: datetime,
                                 time_until: datetime):
        if not os.path.isfile(entity_file):
            entity_type = "Camera" if cls.entity else "Area"
            logger.warn(f"No data for day! [{entity_type}: {entity_id}]")
            return
        objects_logs = {}
        for hour in range(time_from.hour, time_until.hour):
            objects_logs[hour] = {}
        with open(entity_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row_time = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")
                if time_from <= row_time < time_until:
                    cls.procces_csv_row(row, objects_logs)
            return cls.generate_hourly_metric_data(objects_logs)

    @classmethod
    def compute_hourly_metrics(cls, config):
        if not cls.reports_folder:
            raise Exception(f"The metric {cls} doesn't have configured the folder parameter")
        base_directory = get_source_log_directory(config) if cls.entity == "source" else get_area_log_directory(config)
        entities = config.get_video_sources() if cls.entity == "source" else config.get_areas()
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
            if current_hour == 0:
                # Pending to process the latest hour from yesterday
                time_until = datetime.combine(date.today(), time(0, 0))
                report_date = date.today() - timedelta(days=1)
            else:
                time_until = datetime.combine(date.today(), time(current_hour, 0))
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
            csv_data = cls.generate_hourly_csv_data(entity["id"], entity_csv, time_from, time_until)
            if csv_data is None:
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
        base_directory = get_source_log_directory(config) if cls.entity == "source" else get_area_log_directory(config)
        entities = config.get_video_sources() if cls.entity == "source" else config.get_areas()
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
    def generate_live_csv_data(cls, today_entity_csv):
        """
        Generates the live report using the `today_entity_csv` file received.
        """
        raise NotImplementedError

    @classmethod
    def compute_live_metrics(cls, config):
        base_directory = get_source_log_directory(config) if cls.entity == "source" else get_area_log_directory(config)
        entities = config.get_video_sources() if cls.entity == "source" else config.get_areas()
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
            headers = ["Time"] + cls.csv_headers
            report_file_exists = os.path.isfile(live_report_csv)
            if not os.path.isfile(today_entity_csv):
                return
            live_data = cls.generate_live_csv_data(today_entity_csv)
            with open(live_report_csv, "a") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                if not report_file_exists:
                    writer.writeheader()
                row = {"Time": datetime.now()}
                for index, header in enumerate(cls.csv_headers):
                    row[header] = live_data[index]
                writer.writerow(row)
