import cv2 as cv
import numpy as np
import os
import shutil

from libs.utils import visualization_utils
from tools.environment_score import mx_environment_scoring_consider_crowd


class VideoLogger:

    def __init__(self, config, source: str, logger: str):
        self.config = config
        self.camera_id = self.config.get_section_dict(source)["Id"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict("App")["Resolution"].split(",")])
        self.birds_eye_resolution = (200, 300)
        self.out = None
        self.out_birdseye = None

    def start_logging(self, fps):
        self.out, self.out_birdseye = (
            self.gstreamer_writer(feed, fps, resolution)
            for (feed, resolution) in (
                (self.camera_id, self.resolution),
                (self.camera_id + "-birdseye", self.birds_eye_resolution)
            )
        )

    def stop_logging(self):
        self.out.release()
        self.out_birdseye.release()

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

    def update(self, cv_image, objects, distancings, violating_objects, fps):
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
