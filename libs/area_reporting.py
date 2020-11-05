import os
import time
import logging
from libs.loggers.loggers import Logger
from datetime import date, datetime


logger = logging.getLogger(__name__)

class AreaReporting:

    def __init__(self, config, area):
        self.processing_alerts = False
        self.config = config
        self.area_section = area
        self.area = next((area for area in self.config.get_areas() if area['section'] == area), None)

        self.occupancy_sleep_time_interval = float(self.config.get_section_dict("App")["OccupancyAlertsTimeout"])
        self.log_dir = self.config.get_section_dict("Logger")["LogDirectory"]
        self.idle_time = float(self.config.get_section_dict('Logger')['TimeInterval']) + 0.1
        self.area_id = self.area['id']
        self.area_name = self.area['name']
        self.occupancy_threshold = self.area['occupancy_threshold']
        self.emails = self.area['emails']
        self.should_send_email_notifications = self.area['should_send_email_notifications']
        self.should_send_slack_notifications = self.area['should_send_slack_notifications']
        self.camera_ids = self.area['cameras']
        self.cameras = [camera for camera in self.config.get_video_sources() if camera['id'] in self.camera_ids]
        for camera in self.cameras:
            camera['file_path'] = os.path.join(self.log_dir, camera['id'], "objects_log") # , today + ".csv"

        self.logger = Logger(self.config, self.area_id)

    def process_area(self):
        start_time = time.time()
        last_processed_time = time.time()
        today = str(date.today())
        self.processing_alerts = True

        while self.cameras and self.processing_alerts:
            # asd
        self.processing_alerts = False

    def stop_process_area(self):
        self.processing_alerts = False
