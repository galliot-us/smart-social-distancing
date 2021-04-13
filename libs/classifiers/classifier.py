import logging

logging.getLogger().setLevel(logging.INFO)

class Classifier:
    """
    Classifier class is a high level class for classifying images for all devices.
    When an instance of the Classifier is created, it returns a proper classifier
    instance based on your device and you can call inference method and feed your
    input image in order to get the classifier results.
    :param config: Is a ConfigEngine instance which provides necessary parameters.
    """
    def __init__(self, config, source):
        self.config = config
        self.classifier = None
        classifier_section = self.config.get_section_dict("Classifier")
        if classifier_section["Device"] == "Jetson":
            from .jetson.classifier import Classifier as JetClassifier
            self.classifier = JetClassifier(self.config, source)
        elif classifier_section["Device"] == "EdgeTPU":
            from .edgetpu.classifier import Classifier as EdgeClassifier
            self.classifier = EdgeClassifier(self.config)
        elif classifier_section["Device"] in ["x86", "x86-gpu"]:
            from .x86.classifier import Classifier as X86Classifier
            self.classifier = X86Classifier(self.config)
        else:
            raise ValueError(f"Classifier: Not supported device named: {classifier_section['Device']}")
        self.min_threshold = float(self.config.get_section_dict("Classifier").get("MinScore", 0.75))

    def inference(self, objects):
        return self.classifier.inference(objects)

    def object_post_process(self, object, classifier_result, classifier_score):
        if 'face' in object.keys():
            if object['face'] is not None and classifier_score > self.min_threshold:
                object['face_label'] = classifier_result
            else:
                object['face_label'] = -1
