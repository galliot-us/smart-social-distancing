import cv2 as cv
import logging
import numpy as np

from libs.detectors.utils.ml_model_functions import get_model_json_file_or_return_default_values

logger = logging.getLogger(__name__)


class Detector:

    def __init__(self, config, source):
        self.config = config
        self.device = self.config.get_section_dict("Detector")["Device"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict("App")["Resolution"].split(",")])
        self.image_size = [int(i) for i in get_model_json_file_or_return_default_values(
            self.config, self.device, self.config.get_section_dict(source)["Id"])["variables"]["ImageSize"].split(",")]
        self.has_classifier = "Classifier" in self.config.get_sections()
        if self.has_classifier:
            self.classifier_img_size = [
                int(i) for i in self.config.get_section_dict("Classifier")["ImageSize"].split(",")]
            self.classifier_min_img_size = None
            if self.config.get_section_dict("Classifier")["MinImageSize"]:
                self.classifier_min_img_size = [
                    int(i) for i in self.config.get_section_dict("Classifier")["MinImageSize"].split(",")
                ]
        if self.device == "Jetson":
            from .jetson.detector import Detector as JetsonDetector
            self.detector = JetsonDetector(self.config, source)
        elif self.device == "EdgeTPU":
            from .edgetpu.detector import Detector as EdgeTPUDetector
            self.detector = EdgeTPUDetector(self.config, source)
        elif self.device == "Dummy":
            from .dummy.detector import Detector as DummyDetector
            self.detector = DummyDetector(self.config, source)
        elif self.device in ["x86", "x86-gpu"]:
            from libs.detectors.x86.detector import Detector as X86Detector
            self.detector = X86Detector(self.config, source)
        else:
            raise ValueError(f"Detector: Not supported device named: {self.device}")
        if self.device != "Dummy":
            logger.info(f"Device is: {self.device}")
            logger.info(f"Detector is: {self.detector.name}")
            logger.info(f"image size: {self.image_size}")

    @property
    def fps(self):
        if not self.detector:
            return None
        return getattr(self.detector, "fps", None)

    def inference(self, cv_image):
        resized_image = cv.resize(cv_image, tuple(self.image_size[:2]))
        rgb_resized_image = cv.cvtColor(resized_image, cv.COLOR_BGR2RGB)
        object_list = self.detector.inference(rgb_resized_image)
        return self.objects_post_processing(object_list, cv_image)

    def objects_post_processing(self, object_list, cv_image):
        # TODO: Move this logic into the inference implementation in each detector
        [w, h] = self.resolution
        detection_scores = []
        class_ids = []
        detection_bboxes = []
        classifier_objects = []
        for itm in object_list:
            if self.has_classifier and "face" in itm.keys():
                face_bbox = itm["face"]  # [ymin, xmin, ymax, xmax]
                if face_bbox is not None:
                    xmin, xmax = np.multiply([face_bbox[1], face_bbox[3]], self.resolution[0])
                    ymin, ymax = np.multiply([face_bbox[0], face_bbox[2]], self.resolution[1])
                    if (self.classifier_min_img_size
                            and (xmax - xmin < self.classifier_min_img_size[0] or ymax - ymin < self.classifier_min_img_size[1])):
                        # Face is too small to process it, ignore it
                        itm["face"] = None
                    else:
                        croped_face = cv_image[
                            int(ymin):int(ymin) + (int(ymax) - int(ymin)),
                            int(xmin):int(xmin) + (int(xmax) - int(xmin))
                        ]
                        # Resizing input image
                        croped_face = cv.resize(croped_face, tuple(self.classifier_img_size[:2]))
                        croped_face = cv.cvtColor(croped_face, cv.COLOR_BGR2RGB)
                        # Normalizing input image to [0.0-1.0]
                        croped_face = np.array(croped_face) / 255.0
                        classifier_objects.append(croped_face)
            # Prepare tracker input
            box = itm["bbox"]
            x0 = box[1]
            y0 = box[0]
            x1 = box[3]
            y1 = box[2]
            detection_scores.append(itm["score"])
            class_ids.append(int(itm["id"].split("-")[0]))
            detection_bboxes.append((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        classifier_objects = np.array(classifier_objects)
        return object_list, detection_scores, class_ids, detection_bboxes, classifier_objects
