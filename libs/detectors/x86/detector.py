import json
import os
from pathlib import Path


def get_or_create_model_json_file(config, device, camera_id):
    """
    If no model directory was created for a given device, the default values will be taken from the configuration file
    and a model_<device>.json file will be created.
    """
    base_path = os.path.join(config.get_section_dict("App")["EntityConfigDirectory"], "sources", camera_id)
    models_directory_path = os.path.join(base_path, "ml_models")
    json_file_path = os.path.join(models_directory_path, f"model_{device}.json")

    if not os.path.exists(json_file_path):
        # Hypothesis: source config directory (base_path) should always exists.
        if not os.path.exists(models_directory_path):
            Path(models_directory_path).mkdir(parents=True, exist_ok=True)

        # Create .json file
        json_content = {
            "model_name": config.get_section_dict("Detector")["Name"],
            "variables": {
                key: value for key, value in config.get_section_dict("Detector").items() if key not in ["Name", "Device"]
            }
        }
        with open(json_file_path, 'x+') as outfile:
            json.dump(json_content, outfile)
        os.chmod(json_file_path, 0o777)

    with open(json_file_path) as f:
        model_data = json.load(f)

    return model_data


class Detector:
    """
    Detector class is a high level class for detecting object using x86 devices.
    When an instance of the Detector is created you can call inference method and feed your
    input image in order to get the detection results.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param source: A string that represents the camera the camera. Ex: "Source_1".
    """

    def __init__(self, config, source):
        self.config = config
        camera_id = self.config.get_section_dict(source)["Id"]
        device = self.config.get_section_dict("Detector")["Device"]
        model_data = get_or_create_model_json_file(self.config, device, camera_id)

        self.name = model_data["model_name"]

        if self.name == 'mobilenet_ssd_v2':
            from libs.detectors.x86 import mobilenet_ssd
            self.net = mobilenet_ssd.Detector(self.config)
        elif self.name == "openvino":
            from libs.detectors.x86 import openvino
            self.net = openvino.Detector(self.config, self.name, model_data["variables"])
        elif self.name == "openpifpaf":
            from libs.detectors.x86 import openpifpaf
            self.net = openpifpaf.Detector(self.config)
        elif self.name == "openpifpaf_tensorrt":
            from libs.detectors.x86.openpifpaf_tensorrt import openpifpaf_tensorrt
            self.net = openpifpaf_tensorrt.Detector(self.config)
        elif self.name == "yolov3":
            from libs.detectors.x86 import yolov3
            self.net = yolov3.Detector(self.config)

        else:
            raise ValueError('Not supported network named: ', self.name)

    def inference(self, resized_rgb_image):
        self.fps = self.net.fps
        output = self.net.inference(resized_rgb_image)
        return output

