"""
Set of functions related to creating daily and hourly reports of detections and violations.
"""
import os
import argparse
import csv
import schedule
import time
import ast
import numpy as np
import logging

from datetime import date, datetime, timedelta
from libs.config_engine import ConfigEngine
from libs.notifications.slack_notifications import SlackService
from libs.utils.mailing import MailService

logger = logging.getLogger(__name__)


def create_heatmap_report(config, yesterday_csv, heatmap_file, column):
    heatmap_resolution = config.get_section_dict("Logger")["HeatmapResolution"].split(",")
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
                summary[hour] += (1, int(row['DetectedObjects']), int(row['ViolatingObjects']), len(faces), int(sum(faces)))

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


def send_daily_report_notification(config, source):
    log_directory = config.get_section_dict("Logger")["LogDirectory"]
    objects_log_directory = os.path.join(log_directory, source['id'], "objects_log")
    yesterday = str(date.today() - timedelta(days=1))
    daily_csv = os.path.join(objects_log_directory, 'report_' + yesterday + '.csv')
    violations_per_hour = []
    with open(daily_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            violations_per_hour.append(int(row['ViolatingObjects']))
    if sum(violations_per_hour):
        if source['should_send_email_notifications']:
            ms = MailService(config)
            ms.send_daily_report(source['section'], sum(violations_per_hour), violations_per_hour)
        if source['should_send_slack_notifications']:
            camera_name = config.get_section_dict(source['section'])['Name']
            slack_service = SlackService(config)
            slack_service.daily_report(source['id'], camera_name, sum(violations_per_hour))


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)

    if not config.get_boolean('Logger', 'EnableReports'):
        logger.info("Reporting disabled!")
        return
    else:
        logger.info("Reporting enabled!")

    schedule.every().day.at("00:01").do(create_daily_report, config=config)
    sources = config.get_video_sources()
    for src in sources:
        if src['daily_report']:
            schedule.every().day.at(src['daily_report_time']).do(
                send_daily_report_notification, config=config, source=src)

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
