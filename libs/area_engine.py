import os
import time
import logging
import csv

from datetime import date, datetime
from collections import deque

from libs.config_engine import ConfigEngine
from libs.loggers.area_loggers.logger import Logger
from libs.entities.area import Area
from .utils.loggers import get_source_log_directory, get_source_logging_interval
from .utils.mailing import MailService
from .notifications.slack_notifications import SlackService

logger = logging.getLogger(__name__)


class AreaEngine:

    def __init__(self, config: ConfigEngine, area: Area):
        self.processing_alerts = False
        self.config = config
        self.area = area

        self.occupancy_sleep_time_interval = float(self.config.get_section_dict("App")["OccupancyAlertsMinInterval"])
        self.log_dir = get_source_log_directory(config)
        self.idle_time = get_source_logging_interval(config)
        self.area_id = self.area.id
        self.area_name = self.area.name
        self.should_send_email_notifications = self.area.should_send_email_notifications
        self.should_send_slack_notifications = self.area.should_send_slack_notifications
        self.cameras = [camera for camera in self.config.get_video_sources() if camera["id"] in self.area.cameras]
        for camera in self.cameras:
            camera.file_path = os.path.join(self.log_dir, camera["id"], "objects_log")
            camera.last_processed_time = time.time()

        if self.should_send_email_notifications:
            self.mail_service = MailService(config)
        if self.should_send_slack_notifications:
            self.slack_service = SlackService(config)

        self.last_notification_time = 0

        self.loggers = []
        loggers_names = [x for x in self.config.get_sections() if x.startswith("AreaLogger_")]
        for l_name in loggers_names:
            if self.config.get_boolean(l_name, "Enabled"):
                self.loggers.append(Logger(self.config, area.section, l_name))

    def process_area(self):
        # Sleep for a while so cameras start processing
        time.sleep(15)

        self.processing_area = True
        logger.info(f"Enabled processing area - {self.area_id}: {self.area_name} with {len(self.cameras)} cameras")
        while self.processing_area:
            camera_file_paths = [os.path.join(camera.file_path, str(date.today()) + ".csv") for camera in self.cameras]
            if not all(list(map(os.path.isfile, camera_file_paths))):
                # Wait before csv for this day are created
                logger.info(f"Area reporting on - {self.area_id}: {self.area_name} is waiting for reports to be created")
                time.sleep(5)
            else:
                occupancy = 0
                active_cameras = []
                for camera in self.cameras:
                    with open(os.path.join(camera.file_path, str(date.today()) + ".csv"), "r") as log:
                        last_log = deque(csv.DictReader(log), 1)[0]
                        log_time = datetime.strptime(last_log["Timestamp"], "%Y-%m-%d %H:%M:%S")
                        # TODO: If the TimeInterval of the Logger is more than 30 seconds this would have to be revised.
                        if (datetime.now() - log_time).total_seconds() < 30:
                            occupancy += int(last_log["DetectedObjects"])
                            active_cameras.append({"camera_id": camera.id, "camera_name": camera.name})
                        else:
                            logger.warn(f"Logs aren't being updated for camera {camera.id} - {camera.name}")

                for l in self.loggers:
                    l.update(active_cameras, {"occupancy": occupancy})

                threshold = self.area.get_occupancy_threshold(datetime.now())
                if (occupancy > threshold
                        and time.time() - self.last_notification_time > self.occupancy_sleep_time_interval):
                    # Trigger alerts
                    self.last_notification_time = time.time()
                    if self.should_send_email_notifications:
                        self.mail_service.send_occupancy_notification(self.area, occupancy, threshold)
                    if self.should_send_slack_notifications:
                        self.slack_service.occupancy_alert(self.area, occupancy, threshold)
                # Sleep until new data is logged
                time.sleep(self.idle_time)

        self.stop_process_area()

    def stop_process_area(self):
        logger.info(f"Disabled processing area - {self.area_id}: {self.area_name}")
        self.processing_area = False
