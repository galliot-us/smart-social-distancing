import numpy as np
import time

from libs.detectors.utils.ml_model_functions import get_model_json_file_or_return_default_values


class Detector:
    """
    Detects Random bounding boxes

    Detector class is a high level class for detecting object using edgetpu devices.
    When an instance of the Detector is created you can call inference method and feed your
    input image in order to get the detection results.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param source: A string that represents the camera. Ex: "Source_1".
    """

    def __init__(self, config, source):
        self.config = config
        camera_id = self.config.get_section_dict(source)["Id"]
        device = self.config.get_section_dict("Detector")["Device"]
        model_data = get_model_json_file_or_return_default_values(self.config, device, camera_id)

        self.name = model_data["model_name"]
        self.class_id = model_data["variables"]['ClassID']

    def inference(self, resized_rgb_image):
        self.fps = np.random.choice([0.5, 1, 2])
        time.sleep(1.0 / self.fps)
        bbox_transform = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1]]) * 0.5
        class_id = self.class_id
        return [{
            'id': str(class_id)+"-"+str(i),
            'bbox': (bbox_transform @ np.random.rand(4)).tolist(),
            'cls': class_id
        } for i in range(np.random.randint(5))]
