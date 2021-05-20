import time
from libs.uploaders.s3_uploader import S3Uploader


class S3Logger:

    def __init__(self, config, source: str, logger: str):
        self.config = config
        self.screenshot_period = float(self.config.get_section_dict(logger)["ScreenshotPeriod"]) * 60
        self.bucket_screenshots = config.get_section_dict(logger)["ScreenshotS3Bucket"]
        self.camera_id = self.config.get_section_dict(source)['Id']
        self.uploader = S3Uploader()
        self.start_time = time.time()

    # TODO: Make this an async task?
    def capture_violation(self, file_name, cv_image):
        self.uploader.upload_cv_image(self.bucket_screenshots, cv_image, file_name, self.camera_id)

    def update(self, cv_image, objects, post_processing_data, fps, log_time):
        violating_objects = post_processing_data.get("violating_objects", [])
        # Save a screenshot only if the period is greater than 0, a violation is detected, and the minimum period
        # has occured
        if (self.screenshot_period > 0) and (time.time() > self.start_time + self.screenshot_period) and (
                len(violating_objects) > 0):
            self.start_time = time.time()
            self.capture_violation(f"{self.start_time}_violation.jpg", cv_image)

    def start_logging(self, fps):
        pass

    def stop_logging(self):
        pass
