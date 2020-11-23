import numpy as np


class ObjectsFilteringPostProcessor:

    def __init__(self, config, source: str, post_processor: str):
        self.config = config
        self.overlap_threshold = float(
            self.config.get_section_dict(post_processor)["NMSThreshold"]
        )

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
        object_list: a list of dictionaries. each dictionary has attributes of a detected object such
        "id", "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box) and "bbox" (a tuple
        of the normalized (xmin,ymin,xmax,ymax) coordinate of the box)

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

    def filter_objects(self, objects_list):
        new_objects_list = self.ignore_large_boxes(objects_list)
        new_objects_list = self.non_max_suppression_fast(new_objects_list, self.overlap_threshold)
        return new_objects_list
