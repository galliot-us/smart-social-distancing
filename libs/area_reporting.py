import os
import time
import logging
import csv
from datetime import date, datetime
from collections import deque
from .utils.mailing import MailService
from .notifications.slack_notifications import SlackService

logger = logging.getLogger(__name__)


class AreaReporting:

    def __init__(self, config, area):
        self.processing_alerts = False
        self.config = config
        self.area = area

        self.occupancy_sleep_time_interval = float(self.config.get_section_dict("App")["OccupancyAlertsMinInterval"])
        self.log_dir = self.config.get_section_dict("Logger")["LogDirectory"]
        self.idle_time = float(self.config.get_section_dict('Logger')['TimeInterval'])
        self.area_id = self.area['id']
        self.area_name = self.area['name']
        self.occupancy_threshold = self.area['occupancy_threshold']
        self.should_send_email_notifications = self.area['should_send_email_notifications']
        self.should_send_slack_notifications = self.area['should_send_slack_notifications']
        self.cameras = [camera for camera in self.config.get_video_sources() if camera['id'] in self.area['cameras']]
        for camera in self.cameras:
            camera['file_path'] = os.path.join(self.log_dir, camera['id'], "objects_log")
            camera['last_processed_time'] = time.time()

        if self.should_send_email_notifications:
            self.mail_service = MailService(config)
        if self.should_send_slack_notifications:
            self.slack_service = SlackService(config)

    def process_area(self):
        # Sleep for a while so cameras start processing
        time.sleep(30)

        self.processing_alerts = True
        logger.info(f'Enabled processing alerts for - {self.area_id}: {self.area_name} with {len(self.cameras)} cameras')
        while self.processing_alerts:
            camera_file_paths = [os.path.join(camera['file_path'], str(date.today()) + ".csv") for camera in self.cameras]
            if not all(list(map(os.path.isfile, camera_file_paths))):
                # Wait before csv for this day are created
                logger.info(f'Area reporting on - {self.area_id}: {self.area_name} is waiting for reports to be created')
                time.sleep(5)

            occupancy = 0
            for camera in self.cameras:
                with open(os.path.join(camera['file_path'], str(date.today()) + ".csv"), 'r') as log:
                    last_log = deque(csv.DictReader(log), 1)[0]
                    log_time = datetime.strptime(last_log['Timestamp'], "%Y-%m-%d %H:%M:%S")
                    # TODO: If the TimeInterval of the Logger is more than 30 seconds this would have to be revised.
                    if (datetime.now() - log_time).total_seconds() < 30:
                        occupancy += int(last_log['DetectedObjects'])
                    else:
                        logger.warn(f"Logs aren't being updated for camera {camera['id']} - {camera['name']}")

            if occupancy > self.occupancy_threshold:
                # Trigger alerts
                if self.should_send_email_notifications:
                    self.mail_service.send_occupancy_notification(self.area, occupancy)
                if self.should_send_slack_notifications:
                    self.slack_service.occupancy_alert(self.area, occupancy)
                # Sleep until the cooldown of the alert
                time.sleep(self.occupancy_sleep_time_interval)
            else:
                # Sleep until new data is logged
                time.sleep(self.idle_time)

        self.stop_process_area()

    def stop_process_area(self):
        logger.info(f'Disabled processing alerts for area - {self.area_id}: {self.area_name}')
        self.processing_alerts = False
