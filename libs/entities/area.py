import os
import json
from datetime import datetime

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
    def get_global_areas(cls, is_email_enabled, is_slack_enabled, config_dir, area_logs_dir):
        config_path = cls.get_config_path()
        Hay que ver de crear lo que hay en el path, y si no existe crearlo de wanda nara.
        Ver que los test crean esta carpeta: api/tests/data/mocked_data/data/processor/config/areas/
        Capaz fue porque habia fallado el test y no llego al rollback (Fallo xq el append de config daba algo que no retornadba anda ).
        section = None
        title = None
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
