import os
import csv
import operator
import ast
import numpy as np
import logging
import pandas as pd

from datetime import date, datetime, timedelta, time
from libs.notifications.slack_notifications import SlackService, is_slack_configured
from libs.utils.mailing import MailService, is_mailing_configured
from libs.utils.metrics import generate_metrics_from_objects_logs
from libs.utils.loggers import get_source_log_directory

logger = logging.getLogger(__name__)

HOURLY_HEADERS = ["Number", "DetectedObjects", "ViolatingObjects", "DetectedFaces", "UsingFacemask"]
DAILY_HEADERS = ["Date", "Number", "DetectedObjects", "ViolatingObjects", "DetectedFaces", "UsingFacemask"]


def create_heatmap_report(config, yesterday_csv, heatmap_file, column):
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


def process_csv_raw_data(camera_id: str, source_file: str, time_from: datetime, time_until: datetime):
    if not os.path.isfile(source_file):
        logger.warn(f"No data for day! [Camera: {camera_id}]")
        return
    objects_logs = {}
    with open(source_file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_time = datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")
            if time_from <= row_time < time_until:
                row_hour = row_time.hour
                if not objects_logs.get(row_hour):
                    objects_logs[row_hour] = {}
                detections = ast.literal_eval(row["Detections"])
                for index, d in enumerate(detections):
                    if not objects_logs[row_hour].get(d["tracking_id"]):
                        objects_logs[row_hour][d["tracking_id"]] = {
                            "distance_violations": [],
                            "face_labels": []
                        }
                    # Append social distancing violations and face labels
                    objects_logs[row_hour][d["tracking_id"]]["distance_violations"].append(
                        index in ast.literal_eval(row["ViolationsIndexes"]))
                    objects_logs[row_hour][d["tracking_id"]]["face_labels"].append(d.get("face_label", -1))
        summary = generate_metrics_from_objects_logs(objects_logs)
    return summary


def create_hourly_report(config):
    log_directory = get_source_log_directory(config)
    sources = config.get_video_sources()
    current_hour = datetime.now().hour

    for src in sources:
        source_directory = os.path.join(log_directory, src["id"])
        objects_log_directory = os.path.join(source_directory, "objects_log")
        reports_directory = os.path.join(source_directory, "reports")
        # Create missing directories
        os.makedirs(objects_log_directory, exist_ok=True)
        os.makedirs(reports_directory, exist_ok=True)
        if current_hour == 0:
            # Pending to process the latest hour from yesterday
            time_until = datetime.combine(date.today(), time(0, 0))
            report_date = date.today() - timedelta(days=1)
        else:
            time_until = datetime.combine(date.today(), time(current_hour, 0))
            report_date = date.today()
        source_csv = os.path.join(objects_log_directory, str(report_date) + ".csv")
        daily_csv = os.path.join(reports_directory, "report_" + str(report_date) + ".csv")

        time_from = datetime.combine(report_date, time(0, 0))
        if os.path.isfile(daily_csv):
            with open(daily_csv, "r", newline='') as csvfile:
                processed_hours = sum(1 for line in csv.reader(csvfile)) - 1
                time_from = datetime.combine(report_date, time(processed_hours + 1, 0))
        else:
            with open(daily_csv, "a", newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=HOURLY_HEADERS)
                writer.writeheader()

        summary = process_csv_raw_data(src["id"], source_csv, time_from, time_until)
        if summary is None:
            continue
        with open(daily_csv, "a", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HOURLY_HEADERS)
            for item in summary:
                writer.writerow({"Number": item[0], "DetectedObjects": item[1], "ViolatingObjects": item[2],
                                 "DetectedFaces": item[3], "UsingFacemask": item[4]})


def create_daily_report(config):
    log_directory = get_source_log_directory(config)
    sources = config.get_video_sources()
    for src in sources:
        source_directory = os.path.join(log_directory, src["id"])
        objects_log_directory = os.path.join(source_directory, "objects_log")
        heatmaps_directory = os.path.join(source_directory, "heatmaps")
        reports_directory = os.path.join(source_directory, "reports")
        # Create missing directories
        os.makedirs(objects_log_directory, exist_ok=True)
        os.makedirs(heatmaps_directory, exist_ok=True)
        os.makedirs(reports_directory, exist_ok=True)
        yesterday = str(date.today() - timedelta(days=1))
        yesterday_csv = os.path.join(objects_log_directory, yesterday + ".csv")
        hourly_csv = os.path.join(reports_directory, "report_" + yesterday + ".csv")
        report_csv = os.path.join(reports_directory, "report.csv")
        detection_heatmap_file = os.path.join(heatmaps_directory, "detections_heatmap_" + yesterday)
        violation_heatmap_file = os.path.join(heatmaps_directory, "violations_heatmap_" + yesterday)

        if not os.path.isfile(yesterday_csv):
            logger.warn(f"No data for previous day! [Camera: {src['id']}]")
            continue

        if not os.path.isfile(hourly_csv):
            logger.warn(f"Daily report for date {str(yesterday)} not generated! [Camera: {src['id']}]")
            continue

        total_number, total_detections, total_violations, total_faces, total_masks = 0, 0, 0, 0, 0
        with open(hourly_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_number += int(row["Number"])
                total_detections += int(row["DetectedObjects"])
                total_violations += int(row["ViolatingObjects"])
                total_faces += int(row["DetectedFaces"])
                total_masks += int(row["UsingFacemask"])

        report_file_exists = os.path.isfile(report_csv)
        with open(report_csv, "a") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=DAILY_HEADERS)

            if not report_file_exists:
                writer.writeheader()
            writer.writerow(
                {"Date": yesterday, "Number": total_number, "DetectedObjects": total_detections,
                 "ViolatingObjects": total_violations, "DetectedFaces": total_faces, "UsingFacemask": total_masks}
            )
        create_heatmap_report(config, yesterday_csv, detection_heatmap_file, "Detections")
        create_heatmap_report(config, yesterday_csv, violation_heatmap_file, "Violations")


def get_daily_report(config, entity_info, report_date):
    entity_type = entity_info['type']
    all_violations_per_hour = []
    log_directory = get_source_log_directory(config)

    if entity_type == 'Camera':
        objects_log_directory = os.path.join(log_directory, entity_info['id'], "objects_log")
        daily_csv_file_paths = [os.path.join(objects_log_directory, 'report_' + report_date + '.csv')]
    else:
        # entity == 'Area'
        camera_ids = entity_info['cameras']
        daily_csv_file_paths = [
            os.path.join(log_directory, camera_id, "objects_log/report_" + report_date + ".csv") for camera_id in
            camera_ids]

    for file_path in daily_csv_file_paths:
        violations_per_hour = []
        if not os.path.isfile(file_path):
            violations_per_hour = list(np.zeros(24).astype(int))
        else:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    violations_per_hour.append(int(row['ViolatingObjects']))
        if not all_violations_per_hour:
            all_violations_per_hour = violations_per_hour
        else:
            all_violations_per_hour = list(map(operator.add, all_violations_per_hour, violations_per_hour))
    return all_violations_per_hour


def send_daily_report_notification(config, entity_info):
    yesterday = str(date.today() - timedelta(days=1))
    violations_per_hour = get_daily_report(config, entity_info, yesterday)

    if sum(violations_per_hour):
        if is_mailing_configured() and entity_info['should_send_email_notifications']:
            ms = MailService(config)
            ms.send_daily_report(entity_info, sum(violations_per_hour), violations_per_hour)
        if is_slack_configured() and entity_info['should_send_slack_notifications']:
            slack_service = SlackService(config)
            slack_service.daily_report(entity_info, sum(violations_per_hour))


def send_global_report(report_type, config, sources, areas, sources_violations_per_hour, areas_violations_per_hour):
    emails = config.get_section_dict("App")["GlobalReportingEmails"].split(",")
    if is_mailing_configured() and emails:
        ms = MailService(config)
        ms.send_global_report(report_type, sources, areas, sources_violations_per_hour, areas_violations_per_hour)
    if is_slack_configured():
        slack_service = SlackService(config)
        slack_service.send_global_report(report_type, sources, areas, sources_violations_per_hour, areas_violations_per_hour)


def send_daily_global_report(config, sources, areas):
    yesterday = str(date.today() - timedelta(days=1))
    sources_violations_per_hour = [get_daily_report(config, source, yesterday) for source in sources]
    areas_violations_per_hour = [get_daily_report(config, area, yesterday) for area in areas]
    send_global_report('daily', config, sources, areas, sources_violations_per_hour, areas_violations_per_hour)


def send_weekly_global_report(config, sources, areas):
    weekly_sources_violations_per_hour = np.zeros((len(sources), 24))
    weekly_areas_violations_per_hour = np.zeros((len(areas), 24))
    start_week = str(date.today() - timedelta(days=8))
    yesterday = str(date.today() - timedelta(days=1))
    date_range = pd.date_range(start=start_week, end=yesterday)
    for report_date in date_range:
        weekly_sources_violations_per_hour += np.array(
            [get_daily_report(config, source, report_date.strftime('%Y-%m-%d')) for source in sources])
        weekly_areas_violations_per_hour += np.array(
            [get_daily_report(config, area, report_date.strftime('%Y-%m-%d')) for area in areas])
    send_global_report('weekly', config, sources, areas, weekly_sources_violations_per_hour, weekly_areas_violations_per_hour)
