#!/usr/bin/python3
import os
import logging
import configparser
import threading

from libs.utils import config as config_utils
from libs.utils.loggers import get_source_log_directory
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
            if section.startswith(("Source", "PeriodicTask")):
                current_sections.append(section)
            for option, value in options.items():
                self.set_option_in_section(section, option, value)
        for section in self.config.sections():
            if (len(current_sections) and section.startswith(("Source", "PeriodicTask"))
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
                    config_dir = config_utils.get_source_config_directory(self)
                    video_source_logs_dir = get_source_log_directory(self)
                    src = VideoSource(section, title, config_dir, video_source_logs_dir)
                    sources.append(src)
            return sources
        except Exception:
            # Sources are invalid in config file. What should we do?
            raise RuntimeError("Invalid sources in config file")
