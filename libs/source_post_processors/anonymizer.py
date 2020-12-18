import cv2 as cv


class AnonymizerPostProcesor:

    def __init__(self, config, source: str, post_processor: str):
        pass

    def anonymize_image(self, img, objects_list):
        """
        Anonymize every instance in the frame.
        """
        h, w = img.shape[:2]
        for box in objects_list:
            xmin = max(int(box["bboxReal"][0]), 0)
            xmax = min(int(box["bboxReal"][2]), w)
            ymin = max(int(box["bboxReal"][1]), 0)
            ymax = min(int(box["bboxReal"][3]), h)
            ymax = (ymax - ymin) // 3 + ymin
            roi = img[ymin:ymax, xmin:xmax]
            roi = self.anonymize_face(roi)
            img[ymin:ymax, xmin:xmax] = roi
        return img

    @staticmethod
    def anonymize_face(image):
        """
        Blur an image to anonymize the person's faces.
        """
        (h, w) = image.shape[:2]
        kernel_w = int(w / 3)
        kernel_h = int(h / 3)
        if kernel_w % 2 == 0:
            kernel_w = max(1, kernel_w - 1)
        if kernel_h % 2 == 0:
            kernel_h = max(1, kernel_h - 1)
        return cv.GaussianBlur(image, (kernel_w, kernel_h), 0)

    def process(self, cv_image, objects_list, post_processing_data):
        cv_image = self.anonymize_image(cv_image, objects_list)
        return cv_image, objects_list, post_processing_data
