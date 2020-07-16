import pathlib
import time
import os
import numpy as np
import wget
import tensorflow as tf

from libs.detectors.utils.fps_calculator import convert_infr_time_to_fps


def load_model(model_name):
    base_url = 'https://raw.githubusercontent.com/neuralet/neuralet-models/master/amd64/'
    model_file = model_name + "/saved_model/saved_model.pb"
    base_dir = "/repo/data/x86/"
    model_dir = os.path.join(base_dir, model_name)
    if not os.path.isdir(model_dir):
        os.makedirs(os.path.join(model_dir, "saved_model"), exist_ok=True)
        print('model does not exist under: ', model_dir, 'downloading from ', base_url + model_file)
        wget.download(base_url + model_file, os.path.join(model_dir, "saved_model"))

    model_dir = pathlib.Path(model_dir) / "saved_model"

    model = tf.saved_model.load(str(model_dir))
    model = model.signatures['serving_default']

    return model


class Detector:
    """
    Perform object detection with the given model. The model is a quantized tflite
    file which if the detector can not find it at the path it will download it
    from neuralet repository automatically.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    """

    def __init__(self, config):
        self.config = config
        # Get the model name from the config
        self.model_name = self.config.get_section_dict('Detector')['Name']
        # Frames Per Second
        self.fps = None

        self.detection_model = load_model('ped_ssd_mobilenet_v2')

    def inference(self, resized_rgb_image):
        """
        inference function sets input tensor to input image and gets the output.
        The interpreter instance provides corresponding detection output which is used for creating result
        Args:
            resized_rgb_image: uint8 numpy array with shape (img_height, img_width, channels)

        Returns:
            result: a dictionary contains of [{"id": 0, "bbox": [x1, y1, x2, y2], "score":s%}, {...}, {...}, ...]
        """
        input_image = np.expand_dims(resized_rgb_image, axis=0)
        input_tensor = tf.convert_to_tensor(input_image)
        t_begin = time.perf_counter()
        output_dict = self.detection_model(input_tensor)
        inference_time = time.perf_counter() - t_begin  # Seconds

        # Calculate Frames rate (fps)
        self.fps = convert_infr_time_to_fps(inference_time)

        boxes = output_dict['detection_boxes']
        labels = output_dict['detection_classes']
        scores = output_dict['detection_scores']

        class_id = int(self.config.get_section_dict('Detector')['ClassID'])
        score_threshold = float(self.config.get_section_dict('Detector')['MinScore'])
        result = []
        for i in range(boxes.shape[1]):  # number of boxes
            if labels[0, i] == class_id and scores[0, i] > score_threshold:
                result.append({"id": str(class_id) + '-' + str(i), "bbox": boxes[0, i, :], "score": scores[0, i]})

        return result
