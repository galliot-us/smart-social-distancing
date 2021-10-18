import numpy as np


def prepare_detection_results(detections, w, h):
    """
    Change output format of neuralet's Detector class to AlphaPose expected detection output.
    Args:
        object_list: A dictionary contains of [{"id": 0, "bbox": [y1, x1, y2, x2], "score":s%}, {...}, {...}, ...]
        w: Width of input image
        h: Height of input image
    Returns:
        A torch num_of_objects by 8 tensor, each row has the form of
        (batch_index, x_min, y_min, x_max, y_max, detection_score, class_score, 0)
    """
    scale_factors = np.array([w, h, w, h]).astype(np.float32)
    people = [item for item in detections.objects if item.category == "person"]
    num_of_objects = len(people)
    output = np.zeros((num_of_objects, 8), dtype=np.float32)
    output[:, 6] = 0.99
    for i, obj in enumerate(people):
        bbox = np.array([obj.bbox.left, obj.bbox.top, obj.bbox.right, obj.bbox.bottom])
        bbox_scaled = (bbox.astype(np.float32) * scale_factors)
        output[i, 1:5] = bbox_scaled
        output[i, [1, 3]] = np.clip(output[i, [1, 3]], 0.0, w)
        output[i, [2, 4]] = np.clip(output[i, [2, 4]], 0.0, h)
        output[i, 5] = obj.bbox.score

    return output
