import cv2 as cv
import numpy as np
from scipy.spatial.distance import cdist
import math
import os
import shutil
import time
from libs.trackers.iou_tracker import IOUTracker
from libs.loggers.loggers import Logger
from tools.environment_score import mx_environment_scoring_consider_crowd
from tools.objects_post_process import extract_violating_objects
from libs.utils import visualization_utils
from libs.utils.camera_calibration import get_camera_calibration_path
from libs.uploaders.s3_uploader import S3Uploader
import logging
import functools

logger = logging.getLogger(__name__)


class Distancing:

    def __init__(self, config, source, live_feed_enabled=True):
        self.config = config
        self.detector = None
        self.device = self.config.get_section_dict('Detector')['Device']

        self.live_feed_enabled = live_feed_enabled
        self.log_time_interval = float(self.config.get_section_dict("Logger")["TimeInterval"])  # Seconds

        self.classifier = None
        self.classifier_img_size = None
        self.face_mask_classifier = None

        self.running_video = False
        self.tracker = IOUTracker(
            max_lost=int(self.config.get_section_dict("PostProcessor")["MaxLost"]),
            iou_threshold=float(self.config.get_section_dict("PostProcessor")["TrackerIOUThreshold"]),
            min_detection_confidence=0.2,
            max_detection_confidence=1.0
        )
        self.camera_id = self.config.get_section_dict(source)['Id']
        self.logger = Logger(self.config, self.camera_id)
        self.image_size = [int(i) for i in self.config.get_section_dict('Detector')['ImageSize'].split(',')]
        self.default_dist_method = self.config.get_section_dict('PostProcessor')["DefaultDistMethod"]

        if self.config.get_section_dict(source)["DistMethod"]:
            self.dist_method = self.config.get_section_dict(source)["DistMethod"]
        else:
            self.dist_method = self.default_dist_method

        self.dist_threshold = self.config.get_section_dict("PostProcessor")["DistThreshold"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])
        self.birds_eye_resolution = (200, 300)

        if self.dist_method == "CalibratedDistance":
            calibration_file = get_camera_calibration_path(
                self.config, self.config.get_section_dict(source)["Id"])
            try:
                with open(calibration_file, "r") as file:
                    self.h_inv = file.readlines()[0].split(" ")[1:]
                    self.h_inv = np.array(self.h_inv, dtype="float").reshape((3, 3))
            except FileNotFoundError:
                logger.error("The specified 'CalibrationFile' does not exist")
                logger.info(f"Falling back using {self.default_dist_method}")
                self.dist_method = self.default_dist_method

        # config.ini uses minutes as unit
        self.screenshot_period = float(self.config.get_section_dict("App")["ScreenshotPeriod"]) * 60
        self.bucket_screenshots = config.get_section_dict("App")["ScreenshotS3Bucket"]
        self.uploader = S3Uploader(self.config)
        self.screenshot_path = os.path.join(self.config.get_section_dict("App")["ScreenshotsDirectory"], self.camera_id)
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)

        if "Classifier" in self.config.get_sections():
            self.face_threshold = float(self.config.get_section_dict("Classifier").get("MinScore", 0.75))

    def __process(self, cv_image):
        """
        return object_list list of  dict for each obj,
        obj["bbox"] is normalized coordinations for [x0, y0, x1, y1] of box
        """

        # Resize input image to resolution
        cv_image = cv.resize(cv_image, self.resolution)

        resized_image = cv.resize(cv_image, tuple(self.image_size[:2]))
        rgb_resized_image = cv.cvtColor(resized_image, cv.COLOR_BGR2RGB)
        tmp_objects_list = self.detector.inference(rgb_resized_image)

        [w, h] = self.resolution
        detection_scores = []
        class_ids = []
        detection_bboxes = []
        faces = []
        # Get the classifier of detected face
        for itm in tmp_objects_list:
            if 'face' in itm.keys() and self.classifier is not None:
                face_bbox = itm['face']  # [ymin, xmin, ymax, xmax]
                if face_bbox is not None:
                    xmin, xmax = np.multiply([face_bbox[1], face_bbox[3]], self.resolution[0])
                    ymin, ymax = np.multiply([face_bbox[0], face_bbox[2]], self.resolution[1])
                    croped_face = cv_image[
                        int(ymin):int(ymin) + (int(ymax) - int(ymin)),
                        int(xmin):int(xmin) + (int(xmax) - int(xmin))
                    ]

                    # Resizing input image
                    croped_face = cv.resize(croped_face, tuple(self.classifier_img_size[:2]))
                    croped_face = cv.cvtColor(croped_face, cv.COLOR_BGR2RGB)
                    # Normalizing input image to [0.0-1.0]
                    croped_face = np.array(croped_face) / 255.0
                    faces.append(croped_face)
            # Prepare tracker input
            box = itm["bbox"]
            x0 = box[1]
            y0 = box[0]
            x1 = box[3]
            y1 = box[2]
            detection_scores.append(itm['score'])
            class_ids.append(int(itm['id'].split('-')[0]))
            detection_bboxes.append((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
        faces = np.array(faces)
        face_mask_results, scores = self.classifier.inference(faces)

        tracks = self.tracker.update(detection_bboxes, class_ids, detection_scores)
        idx = 0
        for obj in tmp_objects_list:
            if self.classifier is not None and 'face' in obj.keys():
                if obj['face'] is not None and scores[idx] > self.face_threshold:
                    obj['face_label'] = face_mask_results[idx]
                    idx = idx + 1
                else:
                    obj['face_label'] = -1
            box = obj["bbox"]
            x0 = box[1]
            y0 = box[0]
            x1 = box[3]
            y1 = box[2]
            obj["centroid"] = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
            obj["bbox"] = [x0, y0, x1, y1]
            obj["centroidReal"] = [(x0 + x1) * w / 2, (y0 + y1) * h / 2, (x1 - x0) * w, (y1 - y0) * h]
            obj["bboxReal"] = [x0 * w, y0 * h, x1 * w, y1 * h]
            for track in tracks:
                track_count, trackid, class_id_o, centroid, track_bbox, track_info = track
                selected_box = [int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)]
                if functools.reduce(lambda x, y: x and y, map(lambda p, q: p == q, selected_box, track_bbox), True):
                    obj["tracked_id"] = trackid
                    obj["track_info"] = track_info

        objects_list, distancings = self.calculate_distancing(tmp_objects_list)
        anonymize = self.config.get_section_dict('PostProcessor')['Anonymize'] == "true"
        if anonymize:
            cv_image = self.anonymize_image(cv_image, objects_list)
        return cv_image, objects_list, distancings

    def gstreamer_writer(self, feed_name, fps, resolution):
        """
        This method creates and returns an OpenCV Video Writer instance. The VideoWriter expects its `.write()` method
        to be called with a single frame image multiple times. It encodes frames into live video segments and produces
        a video segment once it has received enough frames to produce a 5-seconds segment of live video.
        The video segments are written on the filesystem. The target directory for writing segments is determined by
        `video_root` variable.  In addition to writing the video segments, the VideoWriter also updates a file named
        playlist.m3u8 in the target directory. This file contains the list of generated video segments and is updated
        automatically.
        This instance does not serve these video segments to the client. It is expected that the target video directory
        is being served by a static file server and the clientside HLS video library downloads "playlist.m3u8". Then,
        the client video player reads the link for video segments, according to HLS protocol, and downloads them from
        static file server.

        :param feed_name: Is the name for video feed. We may have multiple cameras, each with multiple video feeds (e.g. one
        feed for visualizing bounding boxes and one for bird's eye view). Each video feed should be written into a
        separate directory. The name for target directory is defined by this variable.
        :param fps: The HLS video player on client side needs to know how many frames should be shown to the user per
        second. This parameter is independent from the frame rate with which the video is being processed. For example,
        if we set fps=60, but produce only frames (by calling `.write()`) per second, the client will see a loading
        indicator for 5*60/30 seconds and then 5 seconds of video is played with fps 60.
        :param resolution: A tuple of size 2 which indicates the resolution of output video.
        """
        encoder = self.config.get_section_dict('App')['Encoder']
        video_root = f'/repo/data/processor/static/gstreamer/{feed_name}'

        shutil.rmtree(video_root, ignore_errors=True)
        os.makedirs(video_root, exist_ok=True)

        playlist_root = f'/static/gstreamer/{feed_name}'
        if not playlist_root.endswith('/'):
            playlist_root = f'{playlist_root}/'
        # the entire encoding pipeline, as a string:
        pipeline = f'appsrc is-live=true !  {encoder} ! mpegtsmux ! hlssink max-files=15 ' \
                   f'target-duration=5 ' \
                   f'playlist-root={playlist_root} ' \
                   f'location={video_root}/video_%05d.ts ' \
                   f'playlist-location={video_root}/playlist.m3u8 '

        out = cv.VideoWriter(
            pipeline,
            cv.CAP_GSTREAMER,
            0, fps, resolution
        )

        if not out.isOpened():
            raise RuntimeError("Could not open gstreamer output for " + feed_name)
        return out

    def process_live_feed(self, cv_image, objects, distancings, violating_objects, out, out_birdseye):
        dist_threshold = float(self.config.get_section_dict("PostProcessor")["DistThreshold"])
        birds_eye_window = np.zeros(self.birds_eye_resolution[::-1] + (3,), dtype="uint8")
        class_id = int(self.config.get_section_dict('Detector')['ClassID'])

        output_dict = visualization_utils.visualization_preparation(objects, distancings, dist_threshold)
        category_index = {class_id: {
            "id": class_id,
            "name": "Pedestrian",
        }}  # TODO: json file for detector config
        face_index = {
            0: "YES",
            1: "NO",
            -1: "N/A",
        }
        # Draw bounding boxes and other visualization factors on input_frame
        visualization_utils.visualize_boxes_and_labels_on_image_array(
            cv_image,
            output_dict["detection_boxes"],
            output_dict["detection_classes"],
            output_dict["detection_scores"],
            output_dict["detection_colors"],
            category_index,
            instance_masks=output_dict.get("detection_masks"),
            use_normalized_coordinates=True,
            line_thickness=3,
            face_labels=output_dict["face_labels"],
            face_index=face_index
        )
        # TODO: Implement perspective view for objects
        birds_eye_window = visualization_utils.birds_eye_view(
            birds_eye_window, output_dict["detection_boxes"], output_dict["violating_objects"])
        try:
            fps = self.detector.fps
        except:
            # fps is not implemented for the detector instance"
            fps = None

        # Put fps to the frame
        # region
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        txt_fps = 'Frames rate = ' + str(fps) + '(fps)'  # Frames rate = 95 (fps)
        # (0, 0) is the top-left (x,y); normalized number between 0-1
        origin = (0.05, 0.93)
        visualization_utils.text_putter(cv_image, txt_fps, origin)
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        # endregion

        # Put environment score to the frame
        # region
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        env_score = mx_environment_scoring_consider_crowd(len(objects), len(violating_objects))
        txt_env_score = 'Env Score = ' + str(env_score)  # Env Score = 0.7
        origin = (0.05, 0.98)
        visualization_utils.text_putter(cv_image, txt_env_score, origin)
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        # endregion

        out.write(cv_image)
        out_birdseye.write(birds_eye_window)

    def process_video(self, video_uri):
        if self.device == 'Jetson':
            from libs.detectors.jetson.detector import Detector
            self.detector = Detector(self.config)
        elif self.device == 'EdgeTPU':
            from libs.detectors.edgetpu.detector import Detector
            from libs.classifiers.edgetpu.classifier import Classifier
            self.detector = Detector(self.config)
            if "Classifier" in self.config.get_sections():
                self.classifier = Classifier(self.config)
                self.classifier_img_size = [int(i) for i in
                                            self.config.get_section_dict("Classifier")["ImageSize"].split(",")]
        elif self.device == 'Dummy':
            from libs.detectors.dummy.detector import Detector
            self.detector = Detector(self.config)
        elif self.device in ['x86', 'x86-gpu']:
            from libs.detectors.x86.detector import Detector
            from libs.classifiers.x86.classifier import Classifier
            self.detector = Detector(self.config)
            if "Classifier" in self.config.get_sections():
                self.classifier = Classifier(self.config)
                self.classifier_img_size = [int(i) for i in
                                            self.config.get_section_dict("Classifier")["ImageSize"].split(",")]

        if self.device != 'Dummy':
            print('Device is: ', self.device)
            print('Detector is: ', self.detector.name)
            print('image size: ', self.image_size)

        input_cap = cv.VideoCapture(video_uri)
        fps = max(25, input_cap.get(cv.CAP_PROP_FPS))

        if (input_cap.isOpened()):
            logger.info(f'opened video {video_uri}')
        else:
            logger.error(f'failed to load video {video_uri}')
            return

        self.running_video = True
        # enable logging gstreamer Errors (https://stackoverflow.com/questions/3298934/how-do-i-view-gstreamer-debug-output)
        os.environ['GST_DEBUG'] = "*:1"
        if self.live_feed_enabled:
            out, out_birdseye = (
                self.gstreamer_writer(feed, fps, resolution)
                for (feed, resolution) in (
                    (self.camera_id, self.resolution),
                    (self.camera_id + '-birdseye', self.birds_eye_resolution)
                )
            )

        dist_threshold = float(self.config.get_section_dict("PostProcessor")["DistThreshold"])
        frame_num = 0
        start_time = time.time()
        last_processed_time = time.time()
        while input_cap.isOpened() and self.running_video:
            _, cv_image = input_cap.read()
            if np.shape(cv_image) != ():
                if not self.live_feed_enabled and (time.time() - last_processed_time < self.log_time_interval):
                    continue
                cv_image, objects, distancings = self.__process(cv_image)
                violating_objects = extract_violating_objects(distancings, dist_threshold)
                if self.live_feed_enabled:
                    self.process_live_feed(cv_image, objects, distancings, violating_objects, out, out_birdseye)
                last_processed_time = time.time()
                frame_num += 1
                if frame_num % 100 == 1:
                    logger.info(f'processed frame {frame_num} for {video_uri}')
                # Save a screenshot only if the period is greater than 0, a violation is detected, and the minimum period
                # has occured
                if (self.screenshot_period > 0) and (time.time() > start_time + self.screenshot_period) and (
                        len(violating_objects) > 0):
                    start_time = time.time()
                    self.capture_violation(f"{start_time}_violation.jpg", cv_image)
                self.save_screenshot(cv_image)
            else:
                continue
            self.logger.update(objects, distancings)
        input_cap.release()
        if self.live_feed_enabled:
            out.release()
            out_birdseye.release()
        del self.detector
        self.running_video = False

    def stop_process_video(self):
        self.running_video = False

    def calculate_distancing(self, objects_list):
        """
        this function post-process the raw boxes of object detector and calculate a distance matrix
        for detected bounding boxes.
        post processing is consist of:
        1. omitting large boxes by filtering boxes which are bigger than the 1/4 of the size the image.
        2. omitting duplicated boxes by applying an auxilary non-maximum-suppression.
        3. apply a simple object tracker to make the detection more robust.

        params:
        object_list: a list of dictionaries. each dictionary has attributes of a detected object such as
        "id", "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box) and "bbox" (a tuple
        of the normalized (xmin,ymin,xmax,ymax) coordinate of the box)

        returns:
        object_list: the post processed version of the input
        distances: a NxN ndarray which i,j element is distance between i-th and l-th bounding box

        """
        new_objects_list = self.ignore_large_boxes(objects_list)
        new_objects_list = self.non_max_suppression_fast(new_objects_list,
                                                         float(self.config.get_section_dict("PostProcessor")[
                                                                   "NMSThreshold"]))
        for i, item in enumerate(new_objects_list):
            item["id"] = item["id"].split("-")[0] + "-" + str(i)
        distances = self.calculate_box_distances(new_objects_list)

        return new_objects_list, distances

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
        cx = boxes[:, 0]
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
            idxs = np.delete(idxs, np.concatenate(([last],
                                                   np.where(overlap > overlapThresh)[0])))
        updated_object_list = [j for i, j in enumerate(object_list) if i in pick]
        return updated_object_list

    def calculate_distance_of_two_points_of_boxes(self, first_point, second_point):

        """
        This function calculates a distance l for two input corresponding points of two detected bounding boxes.
        it is assumed that each person is H = 170 cm tall in real scene to map the distances in the image (in pixels) to
        physical distance measures (in meters).

        params:
        first_point: (x, y, h)-tuple, where x,y is the location of a point (center or each of 4 corners of a bounding box)
        and h is the height of the bounding box.
        second_point: same tuple as first_point for the corresponding point of other box

        returns:
        l:  Estimated physical distance (in centimeters) between first_point and second_point.


        """

        # estimate corresponding points distance
        [xc1, yc1, h1] = first_point
        [xc2, yc2, h2] = second_point

        dx = xc2 - xc1
        dy = yc2 - yc1

        lx = dx * 170 * (1 / h1 + 1 / h2) / 2
        ly = dy * 170 * (1 / h1 + 1 / h2) / 2

        l = math.sqrt(lx ** 2 + ly ** 2)

        return l

    def calculate_box_distances(self, nn_out):

        """
        This function calculates a distance matrix for detected bounding boxes.
        Three methods are implemented to calculate the distances, the first one estimates distance with a calibration matrix
        which transform the points to the 3-d world coordinate, the second one estimates distance of center points of the
        boxes and the third one uses minimum distance of each of 4 points of bounding boxes.

        params:
        object_list: a list of dictionaries. each dictionary has attributes of a detected object such as
        "id", "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and "bboxReal" (a tuple
        of the (xmin,ymin,xmax,ymax) coordinate of the box)

        returns:
        distances: a NxN ndarray which i,j element is estimated distance between i-th and j-th bounding box in real scene (cm)

        """
        if self.dist_method == "CalibratedDistance":
            world_coordinate_points = np.array([self.transform_to_world_coordinate(bbox) for bbox in nn_out])
            if len(world_coordinate_points) == 0:
                distances_asarray = np.array([])
            else:
                distances_asarray = cdist(world_coordinate_points, world_coordinate_points)

        else:
            distances = []
            for i in range(len(nn_out)):
                distance_row = []
                for j in range(len(nn_out)):
                    if i == j:
                        l = 0
                    else:
                        if (self.dist_method == 'FourCornerPointsDistance'):
                            lower_left_of_first_box = [nn_out[i]["bboxReal"][0], nn_out[i]["bboxReal"][1],
                                                       nn_out[i]["centroidReal"][3]]
                            lower_right_of_first_box = [nn_out[i]["bboxReal"][2], nn_out[i]["bboxReal"][1],
                                                        nn_out[i]["centroidReal"][3]]
                            upper_left_of_first_box = [nn_out[i]["bboxReal"][0], nn_out[i]["bboxReal"][3],
                                                       nn_out[i]["centroidReal"][3]]
                            upper_right_of_first_box = [nn_out[i]["bboxReal"][2], nn_out[i]["bboxReal"][3],
                                                        nn_out[i]["centroidReal"][3]]

                            lower_left_of_second_box = [nn_out[j]["bboxReal"][0], nn_out[j]["bboxReal"][1],
                                                        nn_out[j]["centroidReal"][3]]
                            lower_right_of_second_box = [nn_out[j]["bboxReal"][2], nn_out[j]["bboxReal"][1],
                                                         nn_out[j]["centroidReal"][3]]
                            upper_left_of_second_box = [nn_out[j]["bboxReal"][0], nn_out[j]["bboxReal"][3],
                                                        nn_out[j]["centroidReal"][3]]
                            upper_right_of_second_box = [nn_out[j]["bboxReal"][2], nn_out[j]["bboxReal"][3],
                                                         nn_out[j]["centroidReal"][3]]

                            l1 = self.calculate_distance_of_two_points_of_boxes(lower_left_of_first_box,
                                                                                lower_left_of_second_box)
                            l2 = self.calculate_distance_of_two_points_of_boxes(lower_right_of_first_box,
                                                                                lower_right_of_second_box)
                            l3 = self.calculate_distance_of_two_points_of_boxes(upper_left_of_first_box,
                                                                                upper_left_of_second_box)
                            l4 = self.calculate_distance_of_two_points_of_boxes(upper_right_of_first_box,
                                                                                upper_right_of_second_box)

                            l = min(l1, l2, l3, l4)
                        elif (self.dist_method == 'CenterPointsDistance'):
                            center_of_first_box = [nn_out[i]["centroidReal"][0], nn_out[i]["centroidReal"][1],
                                                   nn_out[i]["centroidReal"][3]]
                            center_of_second_box = [nn_out[j]["centroidReal"][0], nn_out[j]["centroidReal"][1],
                                                    nn_out[j]["centroidReal"][3]]

                            l = self.calculate_distance_of_two_points_of_boxes(center_of_first_box,
                                                                               center_of_second_box)
                    distance_row.append(l)
                distances.append(distance_row)
            distances_asarray = np.asarray(distances, dtype=np.float32)
        return distances_asarray

    def transform_to_world_coordinate(self, bbox):
        """
        This function will transform the center of the bottom line of a bounding box from image coordinate to world
        coordinate via a homography matrix
        Args:
            bbox: a dictionary of a  coordinates of a detected instance with "id",
            "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and "bboxReal" (a tuple
            of the (xmin,ymin,xmax,ymax) coordinate of the box) keys

        Returns:
            A numpy array of (X,Y) of transformed point

        """
        floor_point = np.array([int((bbox["bboxReal"][0] + bbox["bboxReal"][2]) / 2), bbox["bboxReal"][3], 1])
        floor_world_point = np.matmul(self.h_inv, floor_point)
        floor_world_point = floor_world_point[:-1] / floor_world_point[-1]
        return floor_world_point

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

    # TODO: Make this an async task?
    def capture_violation(self, file_name, cv_image):
        self.uploader.upload_cv_image(self.bucket_screenshots, cv_image, file_name, self.camera_id)

    def save_screenshot(self, cv_image):
        dir_path = f'{self.screenshot_path}/default.jpg'
        if not os.path.exists(dir_path):
            logger.info(f"Saving default screenshot for {self.camera_id}")
            cv.imwrite(f'{self.screenshot_path}/default.jpg', cv_image)
