import logging

logging.getLogger().setLevel(logging.INFO)

class Classifier:

    def __init__(self, config):
        self.config = config
        self.classifier = None
        classifier_section = self.config.get_section_dict("Classifier")
        if classifier_section["Device"] == "Jetson":
            from .jetson.classifier import Classifier as JetClassifier
            self.classifier = JetClassifier(self.config)
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
        if object['face'] is not None and classifier_score > self.min_threshold:
            object['face_label'] = classifier_result
        else:
            object['face_label'] = -1
