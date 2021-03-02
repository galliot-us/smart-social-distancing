import os
import cv2 as cv
import numpy as np

from pathlib import Path

from ..utils.config import get_source_config_directory
from ..utils.utils import validate_file_exists_and_is_not_empty

class ObjectsFilteringPostProcessor:

    def __init__(self, config, source: str, post_processor: str):
        self.config = config
        self.source = source
        self.overlap_threshold = float(
            self.config.get_section_dict(post_processor)["NMSThreshold"]
        )
        camera_id = config.get_section_dict(source)["Id"]
        roi_file_path = self.get_roi_file_path(camera_id, config)
        self.roi_contour = self.get_roi_contour(roi_file_path)

    @staticmethod
    def ignore_large_boxes(object_list):

        """
        filtering boxes which are biger than the 1/4 of the size the image
        params:
            object_list: a list of dictionaries. each dictionary has attributes of a detected object such as
            "id", "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box) and "bbox" (a tuple
            of the normalized (xmin,ymin,xmax,ymax) coordinate of the box)
        returns:
        object_list: input object list without large boxes
        """
        large_boxes = []
        for i in range(len(object_list)):
            if (object_list[i]["centroid"][2] * object_list[i]["centroid"][3]) > 0.25:
                large_boxes.append(i)
        updated_object_list = [j for i, j in enumerate(object_list) if i not in large_boxes]
        return updated_object_list

    @staticmethod
    def non_max_suppression_fast(object_list, overlapThresh):

        """
        omitting duplicated boxes by applying an auxilary non-maximum-suppression.
        params:
        object_list: a list of dictionaries. each dictionary has attributes of a detected object such "id",
        "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box),
        "bbox" (a tuple of the normalized (xmin,ymin,xmax,ymax) coordinate of the box),
        "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and
        "bboxReal" (a tuple of the (xmin,ymin,xmax,ymax) coordinate of the box)

        overlapThresh: threshold of minimum IoU of to detect two box as duplicated.

        returns:
        object_list: input object list without duplicated boxes
        """
        # if there are no boxes, return an empty list
        boxes = np.array([item["centroid"] for item in object_list])
        corners = np.array([item["bbox"] for item in object_list])
        if len(boxes) == 0:
            return []
        if boxes.dtype.kind == "i":
            boxes = boxes.astype("float")
        # initialize the list of picked indexes
        pick = []
        cy = boxes[:, 1]
        cx = boxes[:, 0] # noqa
        h = boxes[:, 3]
        w = boxes[:, 2]
        x1 = corners[:, 0]
        x2 = corners[:, 2]
        y1 = corners[:, 1]
        y2 = corners[:, 3]
        area = (h + 1) * (w + 1)
        idxs = np.argsort(cy + (h / 2))
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])

            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            # compute the ratio of overlap
            overlap = (w * h) / area[idxs[:last]]
            # delete all indexes from the index list that have
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))
        updated_object_list = [j for i, j in enumerate(object_list) if i in pick]
        return updated_object_list

    @staticmethod
    def is_inside_roi(detected_object, roi_contour):
        """
        An object is inside the RoI if its middle bottom point lies inside it.
        params:
            detected_object: a dictionary, that has attributes of a detected object such as "id",
            "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box),
            "bbox" (a tuple of the normalized (xmin,ymin,xmax,ymax) coordinate of the box),
            "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and
            "bboxReal" (a tuple of the (xmin,ymin,xmax,ymax) coordinate of the box)

            roi_contour: An array of 2-tuples that compose the contour of the RoI
        returns:
        True of False: Depending if the objects coodinates are inside the RoI
        """
        corners = detected_object["bboxReal"]
        x1, x2 = int(corners[0]), int(corners[2])
        y1, y2 = int(corners[1]), int(corners[3])
        if cv.pointPolygonTest(roi_contour, (x1 + (x2-x1)/2, y2), False) >= 0:
            return True
        return False

    @classmethod
    def ignore_objects_outside_roi(cls, objects_list, roi_contour):

        """
        If a Region of Interest is defined, filer boxes which middle bottom point lies outside the RoI.
        params:
            object_list: a list of dictionaries. each dictionary has attributes of a detected object such as
            "id", "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box) and "bbox" (a tuple
            of the normalized (xmin,ymin,xmax,ymax) coordinate of the box)

            roi_contour: An array of 2-tuples that compose the contour of the RoI
        returns:
        object_list: input object list with only the objets that fall under the Region of Interest.
        """

        return [obj for obj in objects_list if cls.is_inside_roi(obj, roi_contour)]

    @staticmethod
    def get_roi_file_path(camera_id, config):
        """ Returns the path to the roi_contour file """
        return f"{get_source_config_directory(config)}/{camera_id}/roi_filtering/roi_contour.csv"

    @staticmethod
    def get_roi_contour(roi_file_path):
        """ Given the path to the roi file it loads it and returns it """
        if validate_file_exists_and_is_not_empty(roi_file_path):
            return np.loadtxt(roi_file_path, delimiter=',', dtype=int)
        else:
            return None

    def filter_objects(self, objects_list):
        new_objects_list = self.ignore_large_boxes(objects_list)
        new_objects_list = self.non_max_suppression_fast(new_objects_list, self.overlap_threshold)
        if self.roi_contour is not None:
            new_objects_list = self.ignore_objects_outside_roi(new_objects_list, self.roi_contour)
        return new_objects_list

    def process(self, cv_image, objects_list, post_processing_data):
        new_objects_list = self.filter_objects(objects_list)
        return cv_image, new_objects_list, post_processing_data
