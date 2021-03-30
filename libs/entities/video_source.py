from .base_entity import BaseEntity


class VideoSource(BaseEntity):

    def __init__(self, config_section: dict, section_title: str, send_email_enabled: bool, send_slack_enabled: bool,
                 config_dir: str, logs_dir: str):
        super().__init__(config_section, section_title, send_email_enabled, send_slack_enabled, config_dir, logs_dir)
        self.type = "Camera"
        self.url = config_section["VideoPath"]
        self.dist_method = config_section["DistMethod"]

        if (self.notify_every_minutes > 0 and self.violation_threshold > 0):
            self.should_send_email_notifications = send_email_enabled and self.emails != []
            self.should_send_slack_notifications = send_slack_enabled and self.enable_slack_notifications
        else:
            self.should_send_email_notifications = False
            self.should_send_slack_notifications = False
