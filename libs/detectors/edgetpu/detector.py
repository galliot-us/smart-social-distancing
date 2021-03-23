from libs.detectors.utils.ml_model_functions import get_model_json_file_or_return_default_values


class Detector:
    """
    Detector class is a high level class for detecting object using edgetpu devices.
    When an instance of the Detector is created you can call inference method and feed your
    input image in order to get the detection results.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param source: A string that represents the camera. Ex: "Source_1".
    """

    def __init__(self, config, source):
        self.config = config
        self.net = None
        self.fps = None
        # Get model name from the config

        camera_id = self.config.get_section_dict(source)["Id"]
        device = self.config.get_section_dict("Detector")["Device"]
        model_data = get_model_json_file_or_return_default_values(self.config, device, camera_id)

        self.name = model_data["model_name"]

        if self.name == 'mobilenet_ssd_v2':  # or mobilenet_ssd_v1
            from . import mobilenet_ssd
            self.net = mobilenet_ssd.Detector(self.config, self.name, model_data["variables"])
        elif self.name == "pedestrian_ssd_mobilenet_v2":
            from . import pedestrian_ssd_mobilenet_v2
            self.net = pedestrian_ssd_mobilenet_v2.Detector(self.config, self.name, model_data["variables"])
        elif self.name == "pedestrian_ssdlite_mobilenet_v2":
            from . import pedestrian_ssdlite_mobilenet_v2
            self.net = pedestrian_ssdlite_mobilenet_v2.Detector(self.config, self.name, model_data["variables"])
        elif self.name == "posenet":
            from . import posenet
            self.net = posenet.Detector(self.config, self.name, model_data["variables"])
        else:
            raise ValueError('Not supported network named: ', self.name)

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
