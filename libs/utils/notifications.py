import os
import csv
from datetime import date, datetime
from threading import Thread
from .mailing import MailService

# Some vars are only used to pass through to mail service/ Maybe this could be refactored.
def check_violations(threshold, config, source_name, camera_id, interval):
    log_dir = config.get_section_dict("Logger")["LogDirectory"]
    today = str(date.today())
    file_path = os.path.join(log_dir, camera_id, "objects_log", today + ".csv")
    now = datetime.today()
    violations = 0
    with open(file_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row_time = datetime.strptime(row['Timestamp'], "%Y-%m-%d %H:%M:%S")
            if ((now - row_time).seconds / 60) < interval:
                violations += int(row['ViolatingObjects'])
    if violations > threshold:
        # send notification
        ms = MailService(config)
        ms.send_violation_notification(source_name, violations)

def run_check_violations(threshold, config, source_name, camera_id, interval):
    job_thread = Thread(target=check_violations, args=[threshold, config, source_name, camera_id, interval])
    job_thread.start()
