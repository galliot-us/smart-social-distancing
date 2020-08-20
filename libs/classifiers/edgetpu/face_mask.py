import os
import time
import numpy as np
import wget

from tflite_runtime.interpreter import load_delegate
from tflite_runtime.interpreter import Interpreter
from ..utils.fps_calculator import convert_infr_time_to_fps


class Classifier:

    def __init__(self, config):
        self.config = config
        # Get the model name from the config
        self.model_name = self.config.get_section_dict('Classifier')['Name']
        # Frames Per Second
        self.fps = None
        self.model_file = 'N/A'
        self.model_path = '/repo/data/edgetpu/' + self.model_file

        # Get the model .tflite file path from the config.
        # If there is no .tflite file in the path it will be downloaded automatically from base_url
        user_model_path = self.config.get_section_dict('Classifier')['ModelPath']
        if len(user_model_path) > 0:
            print('using %s as model' % user_model_path)
            self.model_path = user_model_path
        else:
            base_url = 'N/A'
            url = base_url + self.model_name + '/' + self.model_file

            if not os.path.isfile(self.model_path):
                print('model does not exist under: ', self.model_path, 'downloading from ', url)
                wget.download(url, self.model_path)

        # Load TFLite model and allocate tensors
        self.interpreter = Interpreter(self.model_path, experimental_delegates=[load_delegate("libedgetpu.so.1")])
        self.interpreter.allocate_tensors()
        # Get the model input and output tensor details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # # Get class id from config
        # self.class_id = int(self.config.get_section_dict('')['ClassID'])
        # self.score_threshold = float(self.config.get_section_dict('')['MinScore'])

    def inference(self, resized_rgb_image):
        input_image = np.expand_dims(resized_rgb_image, axis=0)
        # Fill input tensor with input_image
        self.interpreter.set_tensor(self.input_details[0]["index"], input_image)
        t_begin = time.perf_counter()
        self.interpreter.invoke()
        inference_time = time.perf_counter() - t_begin  # Second
        self.fps = convert_infr_time_to_fps(inference_time)
        # The function `get_tensor()` returns a copy of the tensor data.
        # Use `tensor()` in order to get a pointer to the tensor.

        result = []
        return result
