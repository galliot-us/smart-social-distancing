import os
import csv
from datetime import date, datetime
from threading import Thread
from .mailing import MailService
from .loggers import get_source_log_directory
from ..notifications.slack_notifications import SlackService


def get_violations(file_path, interval):
    now = datetime.today()
    violations = 0
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_time = datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S")
            if ((now - row_time).seconds / 60) < interval:
                violations += int(row['ViolatingObjects'])
    return violations


# Some vars are only used to pass through to mail service/ Maybe this could be refactored.
def check_violations(entity_type, threshold, config, entity_info, interval, should_send_email, should_send_slack):
    log_dir = get_source_log_directory(config)
    today = str(date.today())

    violations = 0
    if entity_type == 'Camera':
        file_paths = [os.path.join(log_dir, entity_info.id, "objects_log", today + ".csv")]
    else:
        # entity_type == 'Area'
        camera_ids = entity_info.cameras
        file_paths = [os.path.join(log_dir, camera_id, "objects_log", today + ".csv") for camera_id in camera_ids]

    for file_path in file_paths:
        violations += get_violations(file_path, interval)

    if violations > threshold:
        # send notification
        if should_send_email:
            ms = MailService(config)
            ms.send_violation_notification(entity_info, violations)
        if should_send_slack:
            slack_service = SlackService(config)
            slack_service.violation_report(entity_info, violations)


def run_check_violations(threshold, config, entity_info, interval, should_send_email, should_send_slack):
    entity_type = entity_info.type
    job_thread = Thread(target=check_violations,
                        args=[entity_type, threshold, config, entity_info, interval, should_send_email, should_send_slack])
    job_thread.start()
