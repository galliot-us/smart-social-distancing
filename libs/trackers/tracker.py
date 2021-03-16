import functools

from .base_tracker import BaseTracker
from .iou_tracker import IOUTracker


class Tracker:

    def __init__(self, config):
        self.tracker = None
        self.config = config
        tracker_name = self.config.get_section_dict("Tracker")["Name"]
        if tracker_name == "BaseTracker":
            self.tracker = BaseTracker(int(self.config.get_section_dict("Tracker")["MaxLost"]))
        elif tracker_name == "IOUTracker":
            self.tracker = IOUTracker(
                max_lost=int(self.config.get_section_dict("Tracker")["MaxLost"]),
                iou_threshold=float(self.config.get_section_dict("Tracker")["TrackerIOUThreshold"]),
                min_detection_confidence=0.2,
                max_detection_confidence=1.0
            )
        else:
            raise ValueError(f"Not supported tracker named: {tracker_name}")
        self.resolution = tuple([int(i) for i in self.config.get_section_dict("App")["Resolution"].split(",")])

    def update(self, bboxes: list, class_ids: list, detection_scores: list):
        return self.tracker.update(bboxes, class_ids, detection_scores)

    def object_post_process(self, object: dict, tracks: list):
        [w, h] = self.resolution
        box = object["bbox"]
        x0 = box[1]
        y0 = box[0]
        x1 = box[3]
        y1 = box[2]
        object["centroid"] = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
        object["bbox"] = [x0, y0, x1, y1]
        object["centroidReal"] = [(x0 + x1) * w / 2, (y0 + y1) * h / 2, (x1 - x0) * w, (y1 - y0) * h]
        object["bboxReal"] = [x0 * w, y0 * h, x1 * w, y1 * h]
        for track in tracks:
            track_count, trackid, class_id_o, centroid, track_bbox, track_info = track
            selected_box = [int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)]
            if functools.reduce(lambda x, y: x and y, map(lambda p, q: p == q, selected_box, track_bbox), True):
                object["tracked_id"] = trackid
                object["track_info"] = track_info
