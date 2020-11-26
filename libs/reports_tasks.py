import os
import csv
import operator
import ast
import numpy as np
import logging
import pandas as pd

from datetime import date, datetime, timedelta
from libs.notifications.slack_notifications import SlackService, is_slack_configured
from libs.utils.mailing import MailService, is_mailing_configured

logger = logging.getLogger(__name__)


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


def create_daily_report(config):
    log_directory = config.get_section_dict("Logger")["LogDirectory"]
    sources = config.get_video_sources()
    for src in sources:
        # A directory inside the log_directory that stores object log files.
        objects_log_directory = os.path.join(log_directory, src['id'], "objects_log")
        os.makedirs(objects_log_directory, exist_ok=True)
        yesterday = str(date.today() - timedelta(days=1))
        yesterday_csv = os.path.join(objects_log_directory, yesterday + '.csv')
        daily_csv = os.path.join(objects_log_directory, 'report_' + yesterday + '.csv')
        report_csv = os.path.join(objects_log_directory, 'report.csv')
        detection_heatmap_file = os.path.join(objects_log_directory, 'detections_heatmap_' + yesterday)
        violation_heatmap_file = os.path.join(objects_log_directory, 'violations_heatmap_' + yesterday)

        if os.path.isfile(daily_csv):
            logger.warn("Report was already generated!")
            continue

        if not os.path.isfile(yesterday_csv):
            logger.warn(f"No data for previous day! [Camera: {src['id']}]")
            continue

        summary = np.zeros((24, 5), dtype=np.long)
        with open(yesterday_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                hour = datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S").hour
                detections = ast.literal_eval(row['Detections'])
                faces = [d["face_label"] for d in detections if "face_label" in d]
                masks = [f for f in faces if f == 0]
                summary[hour] += (1, int(row['DetectedObjects']), int(row['ViolatingObjects']), len(faces), len(masks))

        with open(daily_csv, "w", newline='') as csvfile:
            headers = ["Number", "DetectedObjects", "ViolatingObjects", "DetectedFaces", "UsingFacemask"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for item in summary:
                writer.writerow({'Number': item[0], 'DetectedObjects': item[1], 'ViolatingObjects': item[2],
                                 'DetectedFaces': item[3], 'UsingFacemask': item[4]})

        report_file_exists = os.path.isfile(report_csv)
        with open(report_csv, "a") as csvfile:
            headers = ["Date", "Number", "DetectedObjects", "ViolatingObjects", "DetectedFaces", "UsingFacemask"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)

            if not report_file_exists:
                writer.writeheader()
            totals = np.sum(summary, 0)
            writer.writerow(
                {'Date': yesterday, 'Number': totals[0], 'DetectedObjects': totals[1], 'ViolatingObjects': totals[2],
                 'DetectedFaces': totals[3], 'UsingFacemask': totals[4]})

        create_heatmap_report(config, yesterday_csv, detection_heatmap_file, 'Detections')
        create_heatmap_report(config, yesterday_csv, violation_heatmap_file, 'Violations')


def get_daily_report(config, entity_info, report_date):
    entity_type = entity_info['type']
    all_violations_per_hour = []
    log_directory = config.get_section_dict("Logger")["LogDirectory"]

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
