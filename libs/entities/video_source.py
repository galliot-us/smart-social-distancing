from .base_entity import BaseEntity


class VideoSource(BaseEntity):

    def __init__(self, config_section: dict, section_title: str, config_dir: str, logs_dir: str):
        super().__init__(config_section, section_title, config_dir, logs_dir)
        self.type = "Camera"
        self.url = config_section["VideoPath"]
        self.dist_method = config_section["DistMethod"]
