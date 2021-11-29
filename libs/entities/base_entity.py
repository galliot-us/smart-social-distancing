import os
from libs.utils.utils import config_to_boolean


class BaseEntity():

    def __init__(self, config_section: dict, section_title: str, config_dir: str, logs_dir: str):
        self.config_dir = config_dir
        self.section = section_title
        self.id = config_section["Id"]
        self.base_directory = os.path.join(logs_dir, self.id)
        self.name = config_section["Name"]
        if "Tags" in config_section and config_section["Tags"].strip() != "":
            self.tags = config_section["Tags"].split(",")
        else:
            self.tags = []

    def __getitem__(self, key):
        return self.__dict__[key]
