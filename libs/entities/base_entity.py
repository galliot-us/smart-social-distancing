import os
from libs.utils.utils import config_to_boolean


class BaseEntity():

    def __init__(self, config_section: dict, section_title: str, send_email_enabled: bool, send_slack_enabled: bool,
                 config_dir: str, logs_dir: str):
        self.config_dir = config_dir
        self.section = section_title
        self.id = config_section["Id"]
        self.base_directory = os.path.join(logs_dir, self.id)
        self.name = config_section["Name"]
        if "Tags" in config_section and config_section["Tags"].strip() != "":
            self.tags = config_section["Tags"].split(",")
        else:
            self.tags = []
        if "Emails" in config_section and config_section["Emails"].strip() != "":
            self.emails = config_section["Emails"].split(",")
        else:
            self.emails = []
        self.enable_slack_notifications = config_to_boolean(config_section["EnableSlackNotifications"])
        self.notify_every_minutes = int(config_section["NotifyEveryMinutes"])
        self.violation_threshold = int(config_section["ViolationThreshold"])
        self.daily_report = config_to_boolean(config_section["DailyReport"])
        self.daily_report_time = config_section.get("DailyReportTime") or "06:00"

    def __getitem__(self, key):
        return self.__dict__[key]
