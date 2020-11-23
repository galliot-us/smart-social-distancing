import cv2 as cv
import numpy as np
import os
import shutil
import time
from libs.trackers.iou_tracker import IOUTracker
from libs.loggers.loggers import Logger
from tools.environment_score import mx_environment_scoring_consider_crowd
from tools.objects_post_process import extract_violating_objects
from libs.detectors.detector import Detector
from libs.utils import visualization_utils
from libs.uploaders.s3_uploader import S3Uploader
from libs.source_post_processors.social_distance import SocialDistancePostProcessor
from libs.source_post_processors.objects_filtering import ObjectsFilteringPostProcessor
import logging
import functools

logger = logging.getLogger(__name__)


class Distancing:

    def __init__(self, config, source, live_feed_enabled=True):
        self.config = config
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

        self.dist_threshold = self.config.get_section_dict("PostProcessor")["DistThreshold"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])
        self.birds_eye_resolution = (200, 300)

        # config.ini uses minutes as unit
        self.screenshot_period = float(self.config.get_section_dict("App")["ScreenshotPeriod"]) * 60
        self.bucket_screenshots = config.get_section_dict("App")["ScreenshotS3Bucket"]
        self.uploader = S3Uploader(self.config)
        self.screenshot_path = os.path.join(self.config.get_section_dict("App")["ScreenshotsDirectory"], self.camera_id)
        # Store tracks centroids of last 50 frames for visualization, keys are track ids and values are tuples of
        # tracks centroids and corresponding colors
        self.track_hist = dict()
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)

        if "Classifier" in self.config.get_sections():
            from libs.classifiers.edgetpu.classifier import Classifier
            self.face_threshold = float(self.config.get_section_dict("Classifier").get("MinScore", 0.75))
            self.classifier = Classifier(self.config)
            self.classifier_img_size = [
                int(i) for i in self.config.get_section_dict("Classifier")["ImageSize"].split(",")]

        self.distance = SocialDistancePostProcessor(self.config, source, 'SourcePostProcessor_1')
        self.objects_filtering = ObjectsFilteringPostProcessor(self.config, source, 'SourcePostProcessor_0')

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
        self.update_history(tracks)
        tracked_objects_list = []
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
                    tracked_objects_list.append(obj)

        objects_list = self.objects_filtering.filter_objects(tmp_objects_list)
        objects_list, distancings = self.distance.calculate_distancing(objects_list)
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
        # Assign object's color to corresponding track history
        for i, track_id in enumerate(output_dict["track_ids"]):
            self.track_hist[track_id][1].append(output_dict["detection_colors"][i])
        # Draw bounding boxes and other visualization factors on input_frame
        visualization_utils.visualize_boxes_and_labels_on_image_array(
            cv_image,
            output_dict["detection_boxes"],
            output_dict["detection_classes"],
            output_dict["detection_scores"],
            output_dict["detection_colors"],
            output_dict["track_ids"],
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
        fps = self.detector.fps

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

        # visualize tracks
        # region
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        visualization_utils.draw_tracks(cv_image, self.track_hist, radius=1, thickness=1)
        # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
        #endregion

        out.write(cv_image)
        out_birdseye.write(birds_eye_window)

    def process_video(self, video_uri):
        self.detector = Detector(self.config)
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

    def update_history(self, tracks):
        """
        This method updates self.track_hist with new tracks
        """
        _new_track_hist = dict()
        prev_track_ids = list(self.track_hist.keys())
        for track in tracks:
            track_id = track[1]
            if track_id in prev_track_ids:
                prev_centroids = self.track_hist[track_id][0]
                prev_colors = self.track_hist[track_id][1]
                _new_track_hist[track_id] = (np.concatenate((prev_centroids, track[3][None, ...]), axis=0), prev_colors)
                if len(_new_track_hist[track_id][0]) > 50:
                    _new_track_hist[track_id] = (_new_track_hist[track_id][0][1:,:], _new_track_hist[track_id][1][1:])
            else:
                _new_track_hist[track_id] = (track[3][None, ...], [])
        self.track_hist = _new_track_hist
