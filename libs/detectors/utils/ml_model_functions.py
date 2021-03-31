import json
import os
from pathlib import Path
from libs.utils.config import get_source_config_directory


def get_model_json_file_or_return_default_values(config, device, camera_id):
    """
    Check if the json file exists and return the information about the ML model within said file. In case the file does
    not exist, return defaults values from "Detector" in config file.
    """
    base_path = os.path.join(get_source_config_directory(config), camera_id)
    models_directory_path = os.path.join(base_path, "ml_models")
    json_file_path = os.path.join(models_directory_path, f"model_{device}.json")

    # Hypothesis: source config directory (base_path) should always exists.

    if not os.path.exists(json_file_path):
        return {
            "model_name": config.get_section_dict("Detector")["Name"],
            "variables": {
                key: value for key, value in config.get_section_dict("Detector").items() if
                key not in ["Name", "Device"]
            }
        }

    with open(json_file_path) as f:
        model_data = json.load(f)

    return model_data
