from typing import List


class Logger:

    def __init__(self, config, area: str, logger: str):
        logger_name = config.get_section_dict(logger)["Name"]
        self.logger = None
        if logger_name == "file_system_logger":
            from .file_system_logger import FileSystemLogger
            self.logger = FileSystemLogger(config, area, logger)
        else:
            raise ValueError('Not supported logger named: ', logger_name)

    def update(self, cameras: List[str], area_data: dict):
        self.logger.update(cameras, area_data)
