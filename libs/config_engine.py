#!/usr/bin/python3
import os
import logging
import configparser
import threading

from constants import ALL_AREAS
from libs.notifications.slack_notifications import is_slack_configured
from libs.utils.mailing import is_mailing_configured
from libs.utils import config as config_utils
from libs.utils.loggers import get_area_log_directory, get_source_log_directory
from libs.entities.area import Area
from libs.entities.video_source import VideoSource


class ConfigEngine:
    """
    Handle the .ini confige file and provide a convenient interface to read the parameters from config.
    When an instance of ConfigeEngine is created you can use/pass it to other classes/modules that needs
    access to the parameters at config file.

    :param config_path: the path of config file
    """

    def __init__(self, config_path="./config-coral.ini"):
        self.logger = logging.getLogger(__name__)
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config_file_path = config_path
        self.lock = threading.Lock()
        # For dynamic and cross-chapter flexible parameters:
        self.config._interpolation = configparser.ExtendedInterpolation()
        self.section_options_dict = {}
        self._load()

    def set_config_file(self, path):
        self.lock.acquire()
        try:
            self.config.clear()
            self.config_file_path = path
            self._load()
        finally:
            self.lock.release()

    def _load(self):
        self.config = configparser.ConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_file_path)
        for section in self.config.sections():
            self.section_options_dict[section] = {}
            options = self.config.options(section)
            for option in options:
                try:
                    val = self.config.get(section, option)
                    self.section_options_dict[section][option] = val
                    if val == -1:
                        print("skip: %s" % option)
                except Exception:
                    print("exception on %s!" % option)
                    self.section_options_dict[section][option] = None

    def reload(self):
        self.lock.acquire()
        try:
            self._load()
        finally:
            self.lock.release()

    def save(self, path):
        self.lock.acquire()
        try:
            file_obj = open(path, "w")
            self.config.write(file_obj)
            file_obj.close()
        finally:
            self.lock.release()

    def get_section_dict(self, section):
        section_dict = None
        self.lock.acquire()
        try:
            section_dict = self.section_options_dict[section]
        finally:
            self.lock.release()
        return section_dict

    def get_sections(self):
        self.lock.acquire()
        sections = None
        try:
            sections = self.config.sections()
        finally:
            self.lock.release()
        return sections

    def get_boolean(self, section, option):
        result = None
        self.lock.acquire()
        try:
            result = self.config.getboolean(section, option)
        finally:
            self.lock.release()
        return result

    def toggle_boolean(self, section, option):
        self.lock.acquire()
        try:
            val = self.config.getboolean(section, option)
            self.config.set(section, option, str(not val))
        finally:
            self.lock.release()
        self.save(self.config_file_path)

    def set_option_in_section(self, section, option, value):
        self.lock.acquire()
        try:
            if self.config.has_section(section):
                self.config.set(section, option, value)
            else:
                self.config.add_section(section)
                self.config.set(section, option, value)
        finally:
            self.lock.release()

    """
    Receives a dictionary with the sections of the config and options to be updated.
    Saves the new config in the .ini file
    """

    def update_config(self, config, save_file=True):
        current_sections = []
        for section, options in config.items():
            if section.startswith(("Source", "Area", "PeriodicTask")):
                current_sections.append(section)
            for option, value in options.items():
                self.set_option_in_section(section, option, value)
        for section in self.config.sections():
            if (len(current_sections) and section.startswith(("Source", "Area", "PeriodicTask"))
                    and section not in current_sections):
                self.config.remove_section(section)
        self.set_option_in_section("App", "HasBeenConfigured", "True")
        if save_file:
            self.save(self.config_file_path)

    def get_video_sources(self):
        try:
            sources = []
            for title, section in self.config.items():
                if title.startswith("Source_"):
                    is_slack_enabled = self.config["App"]["SlackChannel"] and is_slack_configured()
                    is_email_enabled = is_mailing_configured()
                    config_dir = config_utils.get_source_config_directory(self)
                    video_source_logs_dir = get_source_log_directory(self)
                    src = VideoSource(section, title, is_email_enabled, is_slack_enabled, config_dir,
                                      video_source_logs_dir)
                    sources.append(src)
            return sources
        except Exception:
            # Sources are invalid in config file. What should we do?
            raise RuntimeError("Invalid sources in config file")

    def get_areas(self):
        try:
            areas = []
            cameras_list = []
            is_slack_enabled = self.config["App"]["SlackChannel"] and is_slack_configured()
            is_email_enabled = is_mailing_configured()
            config_dir = config_utils.get_area_config_directory(self)
            area_logs_dir = get_area_log_directory(self)
            for title, section in self.config.items():
                if title.startswith("Area_"):
                    area = Area(section, title, is_email_enabled, is_slack_enabled, config_dir, area_logs_dir)
                    areas.append(area)
                elif title.startswith("Source_"):
                    cameras_list.append(self.config[title]["Id"])
            cameras_string = ",".join(cameras_list)
            areas.append(Area.set_global_area(is_email_enabled, is_slack_enabled, config_dir, area_logs_dir,
                                              cameras_string))
            return areas
        except Exception:
            # Sources are invalid in config file. What should we do?
            raise RuntimeError("Invalid areas in config file")

    def get_area_all(self):
        areas = self.get_areas()
        area_all = next(area for area in areas if area.id == ALL_AREAS)
        return area_all

    def get_area_config_path(self, area_id):
        return os.path.join(config_utils.get_area_config_directory(self), area_id + ".json")

    def should_send_email_notifications(self, entity):
        if "emails" in entity:
            if is_mailing_configured():
                return True
            else:
                self.logger.warning("Tried to enable email notifications but oauth2_cred.json is missing")
        return False

    def should_send_slack_notifications(self, ent):
        if self.config["App"]["SlackChannel"] and ent["enable_slack_notifications"]:
            if is_slack_configured():
                return True
            else:
                self.logger.warning(
                    "Tried to enable slack notifications but slack_token.txt is either missing or unauthorized")
        return False
