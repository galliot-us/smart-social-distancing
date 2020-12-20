import re
import humps
from libs.config_engine import ConfigEngine


# Functions to get values from config file (.ini) -- begin
def get_config_file_json_strings(config_sample_path):
    config_sample = ConfigEngine(config_sample_path)
    sections = config_sample.get_sections()
    config_sample_json = {}

    for section in sections:
        config_sample_json[section] = config_sample.get_section_dict(section)

    config_sample_json = humps.decamelize(config_sample_json)

    return config_sample_json


def json_string_to_json_multi_type_config_file(config_sample_json):
    for key in config_sample_json:
        for key_2 in config_sample_json[key]:
            try:
                config_sample_json[key][key_2] = int(config_sample_json[key][key_2])
            except ValueError:
                if config_sample_json[key][key_2] == "True":
                    config_sample_json[key][key_2] = True
                elif config_sample_json[key][key_2] == "False":
                    config_sample_json[key][key_2] = False
    return config_sample_json


def get_config_file_json(config_sample_path):
    config_sample_json = get_config_file_json_strings(config_sample_path)
    config_sample_json = json_string_to_json_multi_type_config_file(config_sample_json)
    return config_sample_json
# Functions to get values from config file (.ini) -- end


def get_app_from_ini_config_file_json(config_sample_path):
    """Once you have config file in json format, we get the app field."""
    config_sample_json = get_config_file_json(config_sample_path)
    app_json = config_sample_json['app']
    return app_json


def json_multi_type_to_json_string(json_dict):
    """ json_dict is a json with values of all kinds. """
    for key in json_dict:
        json_dict[key] = str(json_dict[key])
    return json_dict


def app_config_file_multi_type_json_to_string_json(app_config):
    response = {}
    for section in app_config:
        section_stringify = json_multi_type_to_json_string(app_config[section])
        response[str(section)] = section_stringify
    return response


def create_app_config(key_value_dict=None):
    default = {"has_been_configured": False,
               "resolution": "string",
               "encoder": "string",
               "max_processes": 0,
               "dashboardurl": "string",
               "screenshots_directory": "/repo/data/processor/static/screenshots",
               "slack_channel": "lanthorn-notifications",
               "occupancy_alerts_min_interval": 180,
               "max_thread_restarts": 0,
               "global_reporting_emails": "email@email,email2@email",
               "global_report_time": "string",
               "daily_global_report": False,
               "weekly_global_report": False,
               "heatmap_resolution": "string"}

    if key_value_dict is not None:
        for key in key_value_dict.keys():
            if key in default.keys():
                default[key] = key_value_dict[key]

    return default


def camel_case_to_snake_case_dict(dictionary):
    di = {}
    for key, value in dictionary.items():
        camel_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
        di[camel_key] = value

    return di
