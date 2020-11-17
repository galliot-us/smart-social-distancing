import abc
import os
import logging
import cv2 as cv
from lxml import etree


class TeacherMetaArch(object):
    """
    base class of teacher models
    """
    def __init__(self, config):
        self.config = config
        self.min_detection = int(self.config.get_section_dict('Teacher')['MinDetectionPerFrame'])
        self.save_frequency = int(self.config.get_section_dict('Teacher')['SaveFrequency'])
        # Frames Per Second
        self.fps = None
        self.image_size = [int(i) for i in self.config.get_section_dict('Teacher')['ImageSize'].split(',')]
        self._name = -1
        # try catch on filling image path and xml path
        self.image_path = self.config.get_section_dict('Teacher')['ImagePath']
        self.xml_path = self.config.get_section_dict('Teacher')['XmlPath']
        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)
        if not os.path.exists(self.xml_path):
            os.makedirs(self.xml_path)
        logging.info("The Images and XML files will be saved under {} and {}".format(self.image_path, self.xml_path))

    @abc.abstractmethod
    def inference(self, preprocessed_image):
        raise NotImplementedError

    def postprocessing(self, raw_results):
        """
        override this method for custom postprocessing and filtering.
        """
        return raw_results

    @property
    def name(self):
        self._name += 1
        return str(self._name)

    def preprocessing(self, image):
        resized_image = cv.resize(image, tuple(self.image_size[:2]))
        preprocessed_image = cv.cvtColor(resized_image, cv.COLOR_BGR2RGB)
        return preprocessed_image

    def save_results(self, image, results):
        """
        store image and teacher predicted bounding boxes based on given frequency and number of detected instances.
        """
        name = self.name
        if (len(results) >= self.min_detection) and (int(name) % self.save_frequency == 0):
            h, w, d = image.shape
            image_info = {"name": name, "w": w, "h": h, "d": d}
            self.write_to_xml(results, image_info)
            self.write_image(image, image_info)

    def convert_to_xml(self, bboxes, image_info):
        """
        this function will create the xml tree from each frame annotation.
        Args:
            bboxes: list of bounding boxes
            image_info: the number of frame that its xml file is creating
        Returns:
            an etree object
        """
        annotation = etree.Element("annotation")
        etree.SubElement(annotation, "filename").text = image_info["name"] + ".jpg"
        size = etree.SubElement(annotation, "size")
        etree.SubElement(size, "width").text = str(image_info["w"])
        etree.SubElement(size, "height").text = str(image_info["h"])
        etree.SubElement(size, "depth").text = str(image_info["d"])
        for bbox in bboxes:
            obj = etree.SubElement(annotation, "object")
            etree.SubElement(obj, "name").text = "pedestrian"
            bounding_box = etree.SubElement(obj, "bndbox")
            etree.SubElement(bounding_box, "xmin").text = bbox[0]
            etree.SubElement(bounding_box, "ymin").text = bbox[1]
            etree.SubElement(bounding_box, "xmax").text = bbox[2]
            etree.SubElement(bounding_box, "ymax").text = bbox[3]
        xml = etree.ElementTree(annotation)
        return xml

    def write_to_xml(self, results, image_info):
        """
        create xml annotation file from teacher prediction output
        Args:
            results: list of dictionary, output of postprocessing method
            image_info: a dictionary contains image size and name.
        """
        w = image_info["w"]
        h = image_info["h"]

        bboxes = []
        for bbox in results:
            x0 = int(bbox["bbox"][0] * w)
            y0 = int(bbox["bbox"][1] * h)
            x1 = int(bbox["bbox"][2] * w)
            y1 = int(bbox["bbox"][3] * h)
            x_min = max(0, x0)
            y_min = max(0, y0)
            x_max = min(w, x1)
            y_max = min(h, y1)
            bboxes.append([str(x_min), str(y_min), str(x_max), str(y_max)])
        xml = self.convert_to_xml(bboxes, image_info)
        xml_file_name = os.path.join(self.xml_path, image_info["name"] + ".xml")
        xml.write(xml_file_name, pretty_print=True)

    def write_image(self, image, image_info):
        """
        save image frame for training purposes
        Args:
            image: input frame
            image_info: a dictionary contains image size and name.
        """

        cv.imwrite(os.path.join(self.image_path, image_info["name"] + ".jpg"), image)
