import collections
import numpy as np
import time
from pose_engine import PoseEngine
from ..utils.fps_calculator import convert_infr_time_to_fps


class Detector:
    """
    Perform pose estimation with Coral's PoseNet. The bounding boxes will be extracted by key-points.
    for more information about PoseNet model go to: https://github.com/google-coral/project-posenet
    :param config: Is a ConfigEngine instance which provides necessary parameters.
    """

    def __init__(self, config):
        self.config = config
        # Get the model name from the config
        self.model_name = self.config.get_section_dict('Detector')['Name']
        # Frames Per Second
        self.fps = None
        self.w, self.h, _ = [int(i) for i in self.config.get_section_dict('Detector')['ImageSize'].split(',')]
        self.engine = PoseEngine(
            f"/project-posenet/models/mobilenet/posenet_mobilenet_v1_075_{self.h}_{self.w}_quant_decoder_edgetpu.tflite"
        )

        # Get class id from config
        self.class_id = int(self.config.get_section_dict('Detector')['ClassID'])
        self.score_threshold = float(self.config.get_section_dict('Detector')['MinScore'])
        self.keypoints = (
            'nose',
            'left eye',
            'right eye',
            'left ear',
            'right ear',
            'left shoulder',
            'right shoulder',
            'left elbow',
            'right elbow',
            'left wrist',
            'right wrist',
            'left hip',
            'right hip',
            'left knee',
            'right knee',
            'left ankle',
            'right ankle'
        )

    def inference(self, resized_rgb_image):
        """
        This method will perform inference and return the detected bounding boxes
        Args:
            resized_rgb_image: uint8 numpy array with shape (img_height, img_width, channels)

        Returns:
            result: a dictionary contains of [{"id": 0, "bbox": [x1, y1, x2, y2], "score":s%}, {...}, {...}, ...]
        """
        assert resized_rgb_image.shape == (self.h, self.w, 3)
        t_begin = time.perf_counter()
        poses, _ = self.engine.DetectPosesInImage(resized_rgb_image)
        inference_time = time.perf_counter() - t_begin  # Second
        self.fps = convert_infr_time_to_fps(inference_time)
        result = []
        for i, pose in enumerate(poses):  # number of boxes
            if pose.score > self.score_threshold:
                pose_dict = collections.OrderedDict(sorted(pose.keypoints.items(), key=lambda x: self.keypoints.index(x[0])))
                keypoints = np.array(
                    [[keypoint.yx[1], keypoint.yx[0], keypoint.score] for _, keypoint in pose_dict.items()])
                pred = keypoints[keypoints[:, 2] > .2]
                xs = pred[:, 0]
                ys = pred[:, 1]
                x_min = int(xs.min())
                x_max = int(xs.max())
                y_min = int(ys.min())
                y_max = int(ys.max())
                w = x_max - x_min
                h = y_max - y_min
                xmin = int(max(x_min - .15 * w, 0))
                xmax = int(min(x_max + .15 * w, self.w))
                ymin = int(max(y_min - .1 * h, 0))
                ymax = int(min(y_max + .1 * h, self.h))
                bbox_dict = {
                    "id": f"{self.class_id}-" + str(i), "bbox": [ymin / self.h, xmin / self.w, ymax / self.h, xmax / self.w],
                    "score": pose.score, "face": None
                }
                # extracting face bounding box
                if np.all(keypoints[[0, 1, 2, 5, 6], -1] > 0.15):
                    x_min_face = int(keypoints[6, 0])
                    x_max_face = int(keypoints[5, 0])
                    y_max_face = int((keypoints[5, 1] + keypoints[6, 1]) / 2)
                    y_eyes = int((keypoints[1, 1] + keypoints[2, 1]) / 2)
                    y_min_face = 2 * y_eyes - y_max_face
                    if (y_max_face - y_min_face > 0) and (x_max_face - x_min_face > 0):
                        h_crop = y_max_face - y_min_face
                        x_min_face = int(max(0, x_min_face - 0.1 * h_crop))
                        y_min_face = int(max(0, y_min_face - 0.1 * h_crop))
                        x_max_face = int(min(self.w, x_min_face + 1.1 * h_crop))
                        y_max_face = int(min(self.h, y_min_face + 1.1 * h_crop))
                        bbox_dict["face"] = [y_min_face / self.h, x_min_face / self.w, y_max_face / self.h, x_max_face / self.w]

                result.append(bbox_dict)

        return result
