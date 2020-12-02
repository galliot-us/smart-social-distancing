class Logger:

    def __init__(self, config, source: str, logger: str, live_feed_enabled: bool):
        logger_name = config.get_section_dict(logger)["Name"]
        self.logger = None
        if logger_name == "video_logger":
            from .video_logger import VideoLogger
            self.logger = VideoLogger(config, source, logger, live_feed_enabled)
        elif logger_name == "s3_logger":
            from .s3_logger import S3Logger
            self.logger = S3Logger(config, source, logger, live_feed_enabled)
        elif logger_name == "file_system_logger":
            from .file_system_logger import FileSystemLogger
            self.logger = FileSystemLogger(config, source, logger, live_feed_enabled)
        elif logger_name == "web_hook_logger":
            from .web_hook_logger import WebHookLogger
            self.logger = WebHookLogger(config, source, logger, live_feed_enabled)
        else:
            raise ValueError('Not supported logger named: ', logger_name)

    def update(self, cv_image, objects, post_processing_data, fps):
        self.logger.update(cv_image, objects, post_processing_data, fps)

    def start_logging(self, fps):
        self.logger.start_logging(fps)

    def stop_logging(self):
        self.logger.stop_logging()
