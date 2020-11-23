import logging

logger = logging.getLogger(__name__)


class Detector:

    def __init__(self, config):
        self.config = config
        self.device = self.config.get_section_dict("Detector")["Device"]
        self.image_size = [int(i) for i in self.config.get_section_dict("Detector")["ImageSize"].split(",")]

        if self.device == "Jetson":
            from .jetson.detector import Detector as JetsonDetector
            self.detector = JetsonDetector(self.config)
        elif self.device == "EdgeTPU":
            from .edgetpu.detector import Detector as EdgeTPUDetector
            self.detector = EdgeTPUDetector(self.config)
        elif self.device == "Dummy":
            from .dummy.detector import Detector as DummyDetector
            self.detector = DummyDetector(self.config)
        elif self.device in ["x86", "x86-gpu"]:
            from libs.detectors.x86.detector import Detector as X86Detector
            self.detector = X86Detector(self.config)
        else:
            raise ValueError(f'Not supported devide named: {self.device}')

        if self.device != "Dummy":
            logger.info(f"Device is: {self.device}")
            logger.info(f"Detector is: {self.detector.name}")
            logger.info(f"image size: {self.image_size}")

    @property
    def fps(self):
        if not self.detector:
            return None
        return getattr(self.detector, 'fps', None)

    def inference(self, resized_rgb_image):
        return self.detector.inference(resized_rgb_image)
