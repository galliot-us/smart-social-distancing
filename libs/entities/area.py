
from .base_entity import BaseEntity
from libs.config_engine import ConfigEngine
from libs.utils.utils import config_to_boolean
from datetime import datetime

class Area(BaseEntity):

    def __init__(self, configSection: dict, section_title: str, send_email_enabled: bool, send_slack_enabled: bool):
        self.section = section_title
        self.id = configSection["id"]
        self.name = configSection["Name"]
        if "Tags" in configSection and configSection["Tags"].strip() != "":
            self.tags = configSection["Tags"].split(",")
        else:
            self.tags = []
        if "Emails" in configSection and configSection["Emails"].strip() != "":
            self.emails = configSection["Emails"].split(",")
        else:
            self.emails = []
        self.enable_slack_notifications = config_to_boolean(configSection["EnableSlackNotifications"])
        self.notify_every_minutes = int(section["NotifyEveryMinutes"])
        self.violation_threshold = int(section["ViolationThreshold"])
        self.daily_report = config_to_boolean(configSection["DailyReport"])
        self.daily_report_time = section.get("DailyReportTime") or "06:00"
        # self.type = "Area"
        self.occupancy_threshold = int(configSection["OccupancyThreshold"])
        if "Cameras" in configSection and configSection["Cameras"].strip() != "":
            self.cameras = configSection["Cameras"].split(",")

        if (self.notify_every_minutes > 0 and self.violation_threshold > 0) or self.occupancy_threshold > 0:
            self.should_send_email_notifications = send_email_enabled and self.emails != []
            self.should_send_slack_notifications = send_slack_enabled and self.enable_slack_notifications
        else:
            self.should_send_email_notifications = False
            self.should_send_slack_notifications = False

    def get_occupancy_threshold(self, date: datetime):
        pass
