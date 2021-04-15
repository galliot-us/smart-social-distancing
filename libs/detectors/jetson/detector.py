
import logging

from libs.detectors.utils.ml_model_functions import get_model_json_file_or_return_default_values

logger = logging.getLogger(__name__)


class Detector:
    """
    Detector class is a high level class for detecting object using NVIDIA jetson devices.
    When an instance of the Detector is created you can call inference method and feed your
    input image in order to get the detection results.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param source: A string that represents the camera. Ex: "Source_1".
    """

    def __init__(self, config, source):
        self.config = config
        self.net = None
        self.fps = None

        camera_id = self.config.get_section_dict(source)["Id"]
        device = self.config.get_section_dict("Detector")["Device"]
        model_data = get_model_json_file_or_return_default_values(self.config, device, camera_id)

        self.name = model_data["model_name"]

        if self.name == 'ssd_mobilenet_v2_coco' or self.name == "ssd_mobilenet_v2_pedestrian_softbio":
            from . import mobilenet_ssd_v2
            self.net = mobilenet_ssd_v2.Detector(self.config, self.name, model_data["variables"])
        elif self.name == "openpifpaf_tensorrt":
            from libs.detectors.jetson.openpifpaf_tensorrt import openpifpaf_tensorrt
            self.net = openpifpaf_tensorrt.Detector(self.config, self.name, model_data["variables"])

        else:
            raise ValueError('Not supported network named: ', self.name)
    
    def __del__(self):
        del self.net

    def inference(self, resized_rgb_image):
        """
        Run inference on an image and get Frames rate (fps)

        Args:
            resized_rgb_image: A numpy array with shape [height, width, channels]

        Returns:
            output: List of objects, each obj is a dict with two keys "id" and "bbox" and "score"
            e.g. [{"id": 0, "bbox": [x1, y1, x2, y2], "score":s%}, {...}, {...}, ...]
        """
        self.fps = self.net.fps
        output = self.net.inference(resized_rgb_image)
        return output
