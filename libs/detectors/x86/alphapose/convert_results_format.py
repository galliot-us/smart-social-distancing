import numpy as np
import torch


def prepare_detection_results(object_list, w, h):
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
    scale_factors = torch.tensor([w, h, w, h])
    num_of_objects = len(object_list)
    output = torch.zeros(num_of_objects, 8, dtype=torch.float32)
    output[:, 6] = 0.99
    for i, obj in enumerate(object_list):
        bbox = torch.tensor([obj["bbox"][1], obj["bbox"][0], obj["bbox"][3], obj["bbox"][2]])
        bbox_scaled = (bbox.float() * scale_factors.float())
        output[i, 1:5] = bbox_scaled
        output[i, [1, 3]] = torch.clamp(output[i, [1, 3]], 0.0, w)
        output[i, [2, 4]] = torch.clamp(output[i, [2, 4]], 0.0, h)
        output[i, 5] = obj["score"]

    return output


def prepare_poses_results(poses, w, h, scores):
    """
    Change the output of AlphaPose estimator format to the Neuralet's Detectors output format.
    Args:
        poses: AlphaPose output, a dictionary with "keypoints", "kp_score", "proposal_score", "idx" and "bbox" keys
        w: Width of input image
        h: Height of input image
        scores: Detection's score

    Returns:
    A dictionary contains of [{"id": 0, "bbox": [y1, x1, y2, x2], "score":s%, "face": [y1, x1, y2, x2]}, {...}, {...}, ...]
    """
    scales = np.array([h, w, h, w])
    results = []
    for i, item in enumerate(poses):
        object_dict = dict()
        bboxes = np.array([item["bbox"][1], item["bbox"][0], item["bbox"][3], item["bbox"][2]])
        bboxes_scaled = np.divide(bboxes, scales)
        object_dict["id"] = "1-" + str(i)
        object_dict["bbox"] = bboxes_scaled.tolist()
        object_dict["score"] = scores[i].item()
        object_dict["face"] = None
        kp_scores = item["kp_score"].numpy()
        keypoints = item["keypoints"]

        # Extract face bounding box
        if np.all(kp_scores[[0, 1, 2, 5, 6]] > 0.15):
            x_min_face = int(keypoints[6, 0])
            x_max_face = int(keypoints[5, 0])
            y_max_face = int((keypoints[5, 1] + keypoints[6, 1]) / 2)
            y_eyes = int((keypoints[1, 1] + keypoints[2, 1]) / 2)
            y_min_face = 2 * y_eyes - y_max_face
            if (y_max_face - y_min_face > 0) and (x_max_face - x_min_face > 0):
                h_crop = y_max_face - y_min_face
                x_min_face = int(max(0, x_min_face - 0.1 * h_crop))
                y_min_face = int(max(0, y_min_face - 0.1 * h_crop))
                x_max_face = int(min(w, x_min_face + 1.1 * h_crop))
                y_max_face = int(min(h, y_min_face + 1.1 * h_crop))
                object_dict["face"] = [y_min_face / h, x_min_face / w, y_max_face / h, x_max_face / w]

        results.append(object_dict)
    return results
