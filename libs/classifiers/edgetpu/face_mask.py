import os
import time
import numpy as np
import wget

from tflite_runtime.interpreter import load_delegate
from tflite_runtime.interpreter import Interpreter
from libs.detectors.utils.fps_calculator import convert_infr_time_to_fps


class Classifier:
    """
    Perform image classification with the given model. The model is an int8 quantized tflite
    file which if the classifier can not find it at the path it will download it
    from neuralet repository automatically.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    """

    def __init__(self, config):
        self.config = config
        # Get the model name from the config
        self.model_name = self.config.get_section_dict('Classifier')['Name']
        # Frames Per Second
        self.fps = None
        self.model_file = 'mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite'  # TODO: remove after testing
        self.model_path = '/repo/data/edgetpu/' + self.model_file

        # Get the model .tflite file path from the config.
        # If there is no .tflite file in the path it will be downloaded automatically from base_url

        # -_- -_- TODO: uncomment when a proper face-mask classifier is available -_- -_-
        # user_model_path = self.config.get_section_dict('Classifier')['ModelPath']
        # if len(user_model_path) > 0:
        #     print('using %s as model' % user_model_path)
        #     self.model_path = user_model_path
        # else:
        #     base_url = 'N/A'
        #     url = base_url + self.model_name + '/' + self.model_file
        #
        #     if not os.path.isfile(self.model_path):
        #         print('model does not exist under: ', self.model_path, 'downloading from ', url)
        #         wget.download(url, self.model_path)
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-

        # Load TFLite model and allocate tensors
        self.interpreter = Interpreter(self.model_path, experimental_delegates=[load_delegate("libedgetpu.so.1")])
        self.interpreter.allocate_tensors()
        # Get the model input and output tensor details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()


    def inference(self, resized_rgb_image):
        """
        Inference function sets input tensor to input image and gets the output.
        The interpreter instance provides corresponding class id output which is used for creating result

        Args:
            resized_rgb_image: List of images with shape (no_images, img_height, img_width, channels)

        Returns:
            result: List of class id for each input image [0, 0, 1, 1, 0]

        """
        if resized_rgb_image == []:
            return resized_rgb_image
        result = []
        
        t_begin = time.perf_counter()
        for img in resized_rgb_image:
            img = img * 255.0
            img = np.array(img, dtype=np.uint8)
            input_image = np.expand_dims(img, axis=0)
            self.interpreter.set_tensor(self.input_details[0]["index"], input_image)
            self.interpreter.invoke()
            out = self.interpreter.get_tensor(self.output_details[0]["index"])
            result.append(int(np.argmax(out)))
            
        inference_time = time.perf_counter() - t_begin  # Second
        self.fps = convert_infr_time_to_fps(inference_time)
        # The function `get_tensor()` returns a copy of the tensor data.
        # Use `tensor()` in order to get a pointer to the tensor.
        return result
