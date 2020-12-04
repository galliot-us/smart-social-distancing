import numpy as np

from typing import List, Tuple

# TODO: In the future maybe make sense allow the users to configure this parameter
PROCESSING_COUNT_THRESHOLD = 3


def process_distance_violation_for_object(distance_violations: List[bool]) -> Tuple[int, int]:
    """
    Receives a list with the "social distancing detections" (for a single person) and returns a
    tuple with the summary of detections and violations. Consecutive detections in the same state are
    grouped and returned as a single one. Detections lower than the constant PROCESSING_COUNT_THRESHOLD
    are ignored.

    For example, the input [True, True, True, True, True, True, False, True, True, True, True, True, False,
    False, False, False, False, False, True, True, True, True, True] returns (3, 2).
    """
    # TODO: This is the first version of the metrics and is implemented to feed the current dashboard.
    # When we define the new metrics we will need to change that logic
    object_detections = 0
    object_violations = 0
    current_status = None
    processing_status = None
    processing_count = 0

    for dist_violation in distance_violations:
        if processing_status != dist_violation:
            processing_status = dist_violation
            processing_count = 0
        processing_count += 1
        if current_status != processing_status and processing_count >= PROCESSING_COUNT_THRESHOLD:
            # Object was enouth time in the same state, change it
            current_status = processing_status
            object_detections += 1
            if current_status:
                # The object was violating the social distance, report it
                object_violations += 1
    return object_detections, object_violations


def process_face_labels_for_object(face_labels: List[int])-> Tuple[int, int]:
    """
    Receives a list with the "facesmask detections" (for a single person) and returns a
    tuple with the summary of faces and mask detected. Consecutive detections in the same state are
    grouped and returned as a single one. Detections lower than the constant PROCESSING_COUNT_THRESHOLD
    are ignored.

    For example, the input [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1 1, 1,
    -1, -1, -1, -1, -1, -1, 0, 0, 0, 0] returns (3, 2).
    """
    # TODO: This is the first version of the metrics and is implemented to feed the current dashboard.
    # When we define the new metrics we will need to change that logic
    face_detections = 0
    mask_detections = 0
    current_status = None
    processing_status = None
    processing_count = 0

    for face_label in face_labels:
        if processing_status != face_label:
            processing_status = face_label
            processing_count = 0
        processing_count += 1
        if current_status != processing_status and processing_count >= PROCESSING_COUNT_THRESHOLD:
            # FaceLabel was enouth time in the same state, change it
            current_status = processing_status
            if current_status != -1:
                # A face was detected
                face_detections += 1
            if current_status == 0:
                # A mask was detected
                mask_detections += 1
    return face_detections, mask_detections


def generate_metrics_from_objects_logs(objects_log):
    # TODO: This is the first version of the metrics and is implemented to feed the current dashboard.
    # When we defined the new metrics we will need to change that logic
    summary = np.zeros((len(objects_log), 5), dtype=np.long)
    for index, hour in enumerate(sorted(objects_log)):
        hour_objects_detections = objects_log[hour]
        for detection_object in hour_objects_detections.values():
            object_detections, object_violations = process_distance_violation_for_object(detection_object["distance_violations"])
            faces_detections, mask_detections = process_face_labels_for_object(detection_object["face_labels"])
            summary[index] += (1, object_detections, object_violations, faces_detections, mask_detections)
    return summary
