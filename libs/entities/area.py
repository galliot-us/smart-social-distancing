import os
import json
from datetime import datetime
import pathlib

from constants import ALL_AREAS
from .base_entity import BaseEntity
from .occupancy_rule import OccupancyRule
from libs.utils.utils import validate_file_exists_and_is_not_empty


class Area(BaseEntity):

    def __init__(self, config_section: dict, section_title: str, send_email_enabled: bool, send_slack_enabled: bool,
                 config_dir: str, logs_dir: str):
        super().__init__(config_section, section_title, send_email_enabled, send_slack_enabled, config_dir, logs_dir)
        self.type = "Area"
        self.occupancy_threshold = int(config_section["OccupancyThreshold"])
        if "Cameras" in config_section and config_section["Cameras"].strip() != "":
            self.cameras = config_section["Cameras"].split(",")

        if (self.notify_every_minutes > 0 and self.violation_threshold > 0) or self.occupancy_threshold > 0:
            self.should_send_email_notifications = send_email_enabled and self.emails != []
            self.should_send_slack_notifications = send_slack_enabled and self.enable_slack_notifications
        else:
            self.should_send_email_notifications = False
            self.should_send_slack_notifications = False
        self.load_occupancy_rules()

    @classmethod
    def set_global_area(cls, is_email_enabled, is_slack_enabled, config_dir, area_logs_dir, cameras_list):
        pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)
        config_path = os.path.join(config_dir, "ALL.json")
        json_content = {
            "global_area_all": {
                "ViolationThreshold": 0,
                "NotifyEveryMinutes": 0,
                "Emails": "",
                "EnableSlackNotifications": False,  # "N/A"
                "DailyReport": False,  # "N/A"
                "DailyReportTime": "N/A",
                "OccupancyThreshold": 0,
                "Id": ALL_AREAS,
                "Name": ALL_AREAS,
            }
        }

        if not os.path.exists(config_path):
            # Create the file with if necessary
            with open(config_path, 'x') as outfile:
                json.dump(json_content, outfile)
            section = json_content["global_area_all"]
        else:
            # If file exists, we have to check if there is a key named: "global_area_all".
            with open(config_path, "r+") as file:
                file_content = json.load(file)

                if file_content.get("global_area_all") is None:
                    file_content["global_area_all"] = json_content["global_area_all"]
                    json.dump(file_content, file)
                    section = json_content["global_area_all"]
                else:
                    section = file_content.get("global_area_all")

        section["Cameras"] = cameras_list
        title = ALL_AREAS

        return Area(section, title, is_email_enabled, is_slack_enabled, config_dir, area_logs_dir)

    def load_occupancy_rules(self):
        self.occupancy_rules = []
        area_config_path = self.get_config_path()
        if validate_file_exists_and_is_not_empty(area_config_path):
            with open(area_config_path) as json_file:
                area_config = json.load(json_file)
            if "occupancy_rules" not in area_config:
                return
            for rule in area_config["occupancy_rules"]:
                self.occupancy_rules.append(OccupancyRule(rule))

    def get_occupancy_threshold(self, date: datetime):
        return next((rule.occupancy_threshold for rule in self.occupancy_rules if rule.date_is_included(date)),
                    self.occupancy_threshold)

    def get_config_path(self):
        return os.path.join(self.config_dir, self.id + ".json")
