import re
import humps
from libs.config_engine import ConfigEngine


def get_config_file_json_strings(config_sample_path, decamelize=False):
    config_sample = ConfigEngine(config_sample_path)
    sections = config_sample.get_sections()
    config_sample_json = {}

    for section in sections:
        config_sample_json[section] = config_sample.get_section_dict(section)

    if decamelize:
        """
        Do not forget that "Source_1" becomes "source__1". 
        """
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


def get_config_file_json(config_sample_path, decamelize=True):
    config_sample_json = get_config_file_json_strings(config_sample_path, decamelize=decamelize)
    config_sample_json = json_string_to_json_multi_type_config_file(config_sample_json)
    return config_sample_json


def pascal_to_camel_case(pascal_case_string: str) -> str:
    if len(pascal_case_string) > 1 and pascal_case_string[1].isupper():
        # pascal_case_string starts with an acronym, returns without change
        return pascal_case_string
    return pascal_case_string[0].lower() + pascal_case_string[1:]


def map_section_from_config(section_name: str, config: dict):
    if section_name not in config:
        return None
    section = config[section_name]
    config_mapped = {}
    for key, value in section.items():
        config_mapped[humps.decamelize(pascal_to_camel_case(key))] = value
    return config_mapped


def section_string_to_section_multi_type(dictionary):
    response = {}
    for key, value in dictionary.items():
        try:
            response[key] = int(dictionary[key])
        except ValueError:
            if dictionary[key] == "True":
                response[key] = True
            elif dictionary[key] == "False":
                response[key] = False
            else:
                response[key] = dictionary[key]
    return response


def get_app_from_config_file(config_sample_path):
    config_sample_json = get_config_file_json_strings(config_sample_path)
    config_mapped_string = map_section_from_config("App", config_sample_json)
    config_mapped = section_string_to_section_multi_type(config_mapped_string)
    return config_mapped


def get_section_from_config_file(section, config_sample_path):
    config_sample_json = get_config_file_json_strings(config_sample_path)
    config_mapped_string = map_section_from_config(section, config_sample_json)
    config_mapped = section_string_to_section_multi_type(config_mapped_string)
    return config_mapped


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
    # "screenshots_directory": "/repo/data/processor/static/screenshots"
    default = {
        "has_been_configured": False,
        "resolution": "string",
        "encoder": "string",
        "max_processes": 0,
        "dashboardurl": "string",
        "slack_channel": "lanthorn-notifications",
        "occupancy_alerts_min_interval": 180,
        "max_thread_restarts": 0,
        "global_reporting_emails": "email@email,email2@email",
        "global_report_time": "string",
        "daily_global_report": False,
        "weekly_global_report": False,
        "log_performance_metrics": False,
        "log_performance_metrics_directory": "/repo/data/processor/static/data/performace-metrics",
        "entity_config_directory": "/repo/data/processor/static/data/config",
        "heatmap_resolution": "string"
    }

    if key_value_dict is not None:
        for key in key_value_dict.keys():
            if key in default.keys():
                default[key] = key_value_dict[key]

    return default


def camel_case_to_snake_case_dict(dictionary):
    di = {}
    for key, value in dictionary.items():
        camel_key = re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()
        di[camel_key] = value

    if "dashboardURL" in dictionary.keys():
        di["dashboardurl"] = dictionary["dashboardURL"]
        del di["dashboard_u_r_l"]

    return di


def create_a_camera(client, camera):
    return client.post("/cameras", json=camera)
