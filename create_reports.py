"""
Set of functions related to creating daily and hourly reports of detections and violations.
"""
import os
import argparse
import csv
import schedule
import time
import sys
import ast
import numpy as np
import logging

from datetime import date, datetime, timedelta
from libs.config_engine import ConfigEngine

logger = logging.getLogger(__name__)


def create_daily_report(config):
    log_directory = config.get_section_dict("Logger")["LogDirectory"]
    heatmap_resolution = config.get_section_dict("Logger")["HeatmapResolution"].split(",")
    heatmap_x = int(heatmap_resolution[0])
    heatmap_y = int(heatmap_resolution[1])
    sources = config.get_video_sources()
    for src in sources:
        # A directory inside the log_directory that stores object log files.
        objects_log_directory = os.path.join(log_directory, src['id'], "objects_log")
        os.makedirs(objects_log_directory, exist_ok=True)
        yesterday = str(date.today() - timedelta(days=1))
        yesterday_csv = os.path.join(objects_log_directory, yesterday + '.csv')
        daily_csv = os.path.join(objects_log_directory, 'report_' + yesterday + '.csv')
        report_csv = os.path.join(objects_log_directory, 'report.csv')
        heatmap_file = os.path.join(objects_log_directory, 'heatmap_' + yesterday)
        heatmap_grid = np.zeros((heatmap_x, heatmap_y))

        if os.path.isfile(daily_csv):
            logger.warn("Report was already generated!")
            continue

        if not os.path.isfile(yesterday_csv):
            logger.warn(f"No data for previous day! [Camera: {src['id']}]")
            continue

        summary = np.zeros((24, 3), dtype=np.long)
        with open(yesterday_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                hour = datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S").hour
                summary[hour] += (1, int(row['DetectedObjects']), int(row['ViolatingObjects']))

        with open(daily_csv, "w", newline='') as csvfile:
            headers = ["Number", "DetectedObjects", "ViolatingObjects"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for item in summary:
                writer.writerow({'Number': item[0], 'DetectedObjects': item[1], 'ViolatingObjects': item[2]})

        report_file_exists = os.path.isfile(report_csv)
        with open(report_csv, "a") as csvfile:
            headers = ["Date", "Number", "DetectedObjects", "ViolatingObjects"]
            writer = csv.DictWriter(csvfile, fieldnames=headers)

            if not report_file_exists:
                writer.writeheader()
            totals = np.sum(summary, 0)
            writer.writerow(
                {'Date': yesterday, 'Number': totals[0], 'DetectedObjects': totals[1], 'ViolatingObjects': totals[2]})

        with open(yesterday_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                detections = ast.literal_eval(row['Detections'])
                for detection in detections:
                    bbox = detection.get('bbox')
                    x = int((np.floor((bbox[0] + bbox[2]) * heatmap_x / 2)).item())
                    y = int((np.floor((bbox[1] + bbox[3]) * heatmap_y / 2)).item())
                    heatmap_grid[x][y] += 1 / (1 + heatmap_grid[x][y])
            np.save(heatmap_file, heatmap_grid)


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

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
