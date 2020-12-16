import os
import csv
import operator
import numpy as np
import pandas as pd
import logging

from datetime import date, timedelta
from libs.notifications.slack_notifications import SlackService, is_slack_configured
from libs.metrics import SocialDistancingMetric
from libs.utils.mailing import MailService, is_mailing_configured
from libs.utils.loggers import get_source_log_directory


logger = logging.getLogger(__name__)


def get_daily_report(config, entity_info, report_date):
    entity_type = entity_info['type']
    all_violations_per_hour = []
    log_directory = get_source_log_directory(config)

    if entity_type == 'Camera':
        reports_directory = os.path.join(log_directory, entity_info['id'], "reports")
        daily_csv_file_paths = [
            os.path.join(reports_directory, SocialDistancingMetric.reports_folder ,'report_' + report_date + '.csv')
        ]
    else:
        # entity == 'Area'
        camera_ids = entity_info['cameras']
        daily_csv_file_paths = [
            os.path.join(log_directory, camera_id, f"reports/{SocialDistancingMetric.reports_folder}/report_" + report_date + ".csv")
            for camera_id in camera_ids]

    for file_path in daily_csv_file_paths:
        violations_per_hour = []
        if not os.path.isfile(file_path):
            violations_per_hour = list(np.zeros(24).astype(int))
        else:
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    violations_per_hour.append(int(row["DetectedObjects"]) - int(row["NoInfringement"]))
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
