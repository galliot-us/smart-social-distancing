import tensorflow as tf
import numpy as np
import wget
import os
import time
from libs.detectors.utils.fps_calculator import convert_infr_time_to_fps


class Classifier:
    """
    Perform image classification with the given model. The model is a .h5 file
    which if the classifier can not find it at the path it will download it
    from neuralet repository automatically.
    :param config: Is a ConfigEngine instance which provides necessary parameters.
    """

    def __init__(self, config):
        self.config = config
        self.model_path = self.config.get_section_dict('Classifier')['ModelPath']

        if len(self.model_path) > 0:
            print('using %s as model' % self.model_path)
        else:
            self.model_path = '/repo/data/x86'
            url = 'https://github.com/neuralet/neuralet-models/raw/master/amd64/OFMClassifier/OFMClassifier.h5'
            model_file = 'OFMClassifier.h5'
            self.model_path = os.path.join(self.model_path, model_file)
            if not os.path.isfile(self.model_path):
                print("model does not exist under: ", self.model_path, 'downloading from ', url)
                wget.download(url, self.model_path)

        self.classifier_model = tf.keras.models.load_model(self.model_path)
        # Frames Per Second
        self.fps = None

    def inference(self, resized_rgb_images) -> list:
        """
        Inference function sets input tensor to input image and gets the output.
        The interpreter instance provides corresponding class id output which is used for creating result
        Args:
            resized_rgb_images: Array of images with shape (no_images, img_height, img_width, channels)
        Returns:
            result: List of class id for each input image. ex: [0, 0, 1, 1, 0]
            scores: The classification confidence for each class. ex: [.99, .75, .80, 1.0]
        """
        if np.shape(resized_rgb_images)[0] == 0:
            return [], []
        # input_image = np.expand_dims(resized_rgb_images, axis=0)
        t_begin = time.perf_counter()
        output_dict = self.classifier_model.predict(resized_rgb_images)
        inference_time = time.perf_counter() - t_begin  # Seconds
        # Calculate Frames rate (fps)
        self.fps = convert_infr_time_to_fps(inference_time)
        result = list(np.argmax(output_dict, axis=1))  # returns class id

        # TODO: optimized without for
        scores = []
        for i, itm in enumerate(output_dict):
            scores.append(itm[result[i]])

        return result, scores
