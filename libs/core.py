import copy
import cv2 as cv
import numpy as np
import math

from libs import pubsub
from libs.centroid_object_tracker import CentroidTracker
from libs.loggers.loggers import Logger
from tools.environment_score import mx_environment_scoring_consider_crowd
from tools.objects_post_process import extract_violating_objects
from ui.utils import visualization_utils


class Distancing:

    def __init__(self, config):
        self.config = config
        self.detector = None
        self.device = self.config.get_section_dict('Detector')['Device']
        self.running_video = False
        self.tracker = CentroidTracker(
            max_disappeared=int(self.config.get_section_dict("PostProcessor")["MaxTrackFrame"]))
        self.logger = Logger(self.config)
        if self.device == 'Jetson':
            from libs.detectors.jetson.detector import Detector
            self.detector = Detector(self.config)
        elif self.device == 'EdgeTPU':
            from libs.detectors.edgetpu.detector import Detector
            self.detector = Detector(self.config)
        elif self.device == 'Dummy':
            from libs.detectors.dummy.detector import Detector
            self.detector = Detector(self.config)
        elif self.device == 'x86':
            from libs.detectors.x86.detector import Detector
            self.detector = Detector(self.config)

        self.image_size = [int(i) for i in self.config.get_section_dict('Detector')['ImageSize'].split(',')]

        if self.device != 'Dummy':
            print('Device is: ', self.device)
            print('Detector is: ', self.detector.name)
            print('image size: ', self.image_size)

        self.dist_method = self.config.get_section_dict("PostProcessor")["DistMethod"]
        self.dist_threshold = self.config.get_section_dict("PostProcessor")["DistThreshold"]
        self.resolution = tuple([int(i) for i in self.config.get_section_dict('App')['Resolution'].split(',')])
        self.calibration_frames = int(self.config.get_section_dict("PostProcessor")["CalibrationFrames"])
        self.box_priors = WelfordBoxDist(*self.resolution)
        self.background_subtractor = cv.createBackgroundSubtractorMOG2()


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
        self.foreground_mask = self.background_subtractor.apply(cv_image)
        self.foreground_mask = cv.threshold(self.foreground_mask, 128, 255, cv.THRESH_BINARY)[1] / 255
        [w, h] = self.resolution

        for obj in tmp_objects_list:
            box = obj["bbox"]
            x0 = box[1]
            y0 = box[0]
            x1 = box[3]
            y1 = box[2]
            obj["centroid"] = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
            obj["bbox"] = [x0, y0, x1, y1]
            obj["centroidReal"]=[(x0 + x1)*w / 2, (y0 + y1)*h / 2, (x1 - x0)*w, (y1 - y0)*h]
            obj["bboxReal"]=[x0*w,y0*h,x1*w,y1*h]
 
        objects_list, distancings = self.calculate_distancing(tmp_objects_list)
        return cv_image, objects_list, distancings

    def process_video(self, video_uri):
        input_cap = cv.VideoCapture(video_uri)

        if (input_cap.isOpened()):
            print('opened video ', video_uri)
        else:
            print('failed to load video ', video_uri)
            return

        self.running_video = True

        dist_threshold = float(self.config.get_section_dict("PostProcessor")["DistThreshold"])
        class_id = int(self.config.get_section_dict('Detector')['ClassID'])

        send = pubsub.init_publisher('default')  # TODO hossein: replace default with camera-id in multi-camera
        send_birds_eye = pubsub.init_publisher('default-birdseye')
        while input_cap.isOpened() and self.running_video:
            _, cv_image = input_cap.read()
            birds_eye_window = np.zeros((300, 200, 3), dtype="uint8")
            if np.shape(cv_image) != ():
                cv_image, objects, distancings = self.__process(cv_image)
                output_dict = visualization_utils.visualization_preparation(objects, distancings, dist_threshold)

                category_index = {class_id: {
                    "id": class_id,
                    "name": "Pedestrian",
                }}  # TODO: json file for detector config
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
                )
                # TODO: Implement perspective view for objects
                birds_eye_window = visualization_utils.birds_eye_view(birds_eye_window, output_dict["detection_boxes"],
                                                           output_dict["violating_objects"])
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
                violating_objects = extract_violating_objects(distancings, dist_threshold)
                env_score = mx_environment_scoring_consider_crowd(len(objects), len(violating_objects))
                txt_env_score = 'Env Score = ' + str(env_score)  # Env Score = 0.7
                origin = (0.05, 0.98)
                visualization_utils.text_putter(cv_image, txt_env_score, origin)
                # -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_- -_-
                # endregion

                _, cv_image = cv.imencode(".jpeg", cv_image)
                _, birds_eye_window = cv.imencode(".jpeg", birds_eye_window)
                send(bytearray(cv_image))
                send_birds_eye(bytearray(birds_eye_window))
            else:
                continue
            self.logger.update(objects, distancings)
        input_cap.release()
        self.running_video = False

    def calculate_distancing(self, objects_list):
        """
        this function post-process the raw boxes of object detector and calculate a distance matrix
        for detected bounding boxes.
        post processing is consist of:
        1. omitting large boxes by filtering boxes which are biger than the 1/4 of the size the image.
        2. omitting duplicated boxes by applying an auxilary non-maximum-suppression.
        3. apply a simple object tracker to make the detection more robust.
        4. filter bounding boxes based on boxes prior distribution.
        5. filter bounding boxes based on the amount of foreground pixels exist on the box.

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
        new_objects_list = self.filter_boxes(new_objects_list)
        tracked_boxes = self.tracker.update(new_objects_list)
        new_objects_list = [tracked_boxes[i] for i in tracked_boxes.keys()]
        for i, item in enumerate(new_objects_list):
            item["id"] = item["id"].split("-")[0] + "-" + str(i)

        centroids = np.array( [obj["centroid"] for obj in new_objects_list] )
        distances = self.calculate_box_distances(new_objects_list)

        return new_objects_list, distances

    def filter_boxes(self, objects_list):
        """
        filter bounding boxes based on boxes prior distribution and amount of foreground pixels exist in the box.
        there is a training phase where the prior means and standard deviations and background/foreground distribution
        will be calculated and then this distribution will be used to filter the bounding boxes.
        params:
        objects_list: A list of dictionaries. each dictionary has attributes of a detected object such as
        "id", "centroid" (a tuple of the normalized centroid coordinates (cx,cy,w,h) of the box) and "bbox" (a tuple
        of the normalized (xmin,ymin,xmax,ymax) coordinate of the box)

        returns:
        objects_list: a filtered version of input

        """

        if self.box_priors.num_calls < self.calibration_frames:  # self.calibration_frames is training number of frames.
            self.box_priors.update(objects_list)
        else:
            if self.box_priors.num_calls == self.calibration_frames:
                self.box_priors.compute_stats()
            objects_list_copy = copy.copy(objects_list)
            for box in objects_list_copy:
                cx, cy, w, h = [int(i) for i in box["centroidReal"]]
                cx = min(cx, self.resolution[0] - 1)
                cy = min(cy, self.resolution[1] - 1)
                # for filtering criteria we used three-sigma rule and additional condition that ensures that
                # enough number of boxes has been detected in training phase for a centroid pixel.
                condition_w = self.box_priors.mean[0, cy, cx] - 3 * self.box_priors.std[0, cy, cx] <\
                              w\
                              < self.box_priors.mean[0, cy, cx] + 3 * self.box_priors.std[0, cy, cx]
                condition_h = self.box_priors.mean[1, cy, cx] - 3 * self.box_priors.std[1, cy, cx] <\
                              h\
                              < self.box_priors.mean[1, cy, cx] + 3 * self.box_priors.std[1, cy, cx]
                if (not (condition_w and condition_h)) and self.box_priors.count[cy, cx] > 10:
                    objects_list.remove(box)
                    continue
                # ========================================================================================== #
                # filtering based on number of foreground pixel
                # ========================================================================================== #
                x_min = max(0, int(box["bboxReal"][0]))
                y_min = max(0, int(box["bboxReal"][1]))
                x_max = min(self.resolution[0] - 1, int(box["bboxReal"][2]))
                y_max = min(self.resolution[1] - 1, int(box["bboxReal"][3]))
                bbox_mask_window = self.foreground_mask[y_min:y_max, x_min:x_max]
                foreground_portion = bbox_mask_window.sum() / bbox_mask_window.size
                if foreground_portion < .1:
                    objects_list.remove(box)
        return objects_list




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


    def calculate_distance_of_two_points_of_boxes(self,first_point, second_point):
    
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
        
        lx = dx * 170 * (1/h1 + 1/h2)/2
        ly = dy * 170 * (1/h1 + 1/h2)/2
        
        l=math.sqrt(lx**2+ly**2)
        
        return l 

    def calculate_box_distances(self, nn_out):
        
        """
        This function calculates a distance matrix for detected bounding boxes.
        Two methods are implemented to calculate the distances, first one estimates distance of center points of the
        boxes and second one uses minimum distance of each of 4 points of bounding boxes.

        params:
        object_list: a list of dictionaries. each dictionary has attributes of a detected object such as
        "id", "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and "bboxReal" (a tuple
        of the (xmin,ymin,xmax,ymax) coordinate of the box)

        returns:
        distances: a NxN ndarray which i,j element is estimated distance between i-th and j-th bounding box in real scene (cm)

        """

        distances = []
        for i in range(len(nn_out)):
            distance_row=[]
            for j in range(len(nn_out)):
                if i == j:
                    l = 0
                else:
                    if ( self.dist_method == 'FourCornerPointsDistance' ):
                        lower_left_of_first_box = [nn_out[i]["bboxReal"][0],nn_out[i]["bboxReal"][1],nn_out[i]["centroidReal"][3]]
                        lower_right_of_first_box = [nn_out[i]["bboxReal"][2],nn_out[i]["bboxReal"][1],nn_out[i]["centroidReal"][3]]
                        upper_left_of_first_box = [nn_out[i]["bboxReal"][0],nn_out[i]["bboxReal"][3],nn_out[i]["centroidReal"][3]]
                        upper_right_of_first_box = [nn_out[i]["bboxReal"][2],nn_out[i]["bboxReal"][3],nn_out[i]["centroidReal"][3]]
                        
                        lower_left_of_second_box = [nn_out[j]["bboxReal"][0],nn_out[j]["bboxReal"][1],nn_out[j]["centroidReal"][3]]
                        lower_right_of_second_box = [nn_out[j]["bboxReal"][2],nn_out[j]["bboxReal"][1],nn_out[j]["centroidReal"][3]]
                        upper_left_of_second_box = [nn_out[j]["bboxReal"][0],nn_out[j]["bboxReal"][3],nn_out[j]["centroidReal"][3]]
                        upper_right_of_second_box = [nn_out[j]["bboxReal"][2],nn_out[j]["bboxReal"][3],nn_out[j]["centroidReal"][3]]

                        l1 = self.calculate_distance_of_two_points_of_boxes(lower_left_of_first_box, lower_left_of_second_box)
                        l2 = self.calculate_distance_of_two_points_of_boxes(lower_right_of_first_box, lower_right_of_second_box)
                        l3 = self.calculate_distance_of_two_points_of_boxes(upper_left_of_first_box, upper_left_of_second_box)
                        l4 = self.calculate_distance_of_two_points_of_boxes(upper_right_of_first_box, upper_right_of_second_box)
                        
                        l = min(l1, l2, l3, l4)
                    elif ( self.dist_method == 'CenterPointsDistance' ):
                        center_of_first_box = [nn_out[i]["centroidReal"][0],nn_out[i]["centroidReal"][1],nn_out[i]["centroidReal"][3]]
                        center_of_second_box = [nn_out[j]["centroidReal"][0],nn_out[j]["centroidReal"][1],nn_out[j]["centroidReal"][3]]

                        l = self.calculate_distance_of_two_points_of_boxes(center_of_first_box, center_of_second_box) 
                distance_row.append(l)    
            distances.append(distance_row)
        distances_asarray = np.asarray(distances, dtype=np.float32)
        return distances_asarray


class WelfordBoxDist:
    """
    This module will compute the mean, variance and standard deviation of width and height of bounding boxes for each
    centroid point recurrently with Welford algorithm.
    params:
    img_width: width of the desired output frame
    img_height: width of the desired output frame
    """
    def __init__(self, img_width, img_height):
        self.mean = np.zeros((2, img_height, img_width))
        self.m2 = np.ones((2, img_height, img_width))
        self.count = np.zeros((img_height, img_width), dtype=int)
        self.num_calls = 0
        self.img_width = img_width
        self.img_height = img_height

    def update(self, new_objects):
        """
        this method will update the mean and the numerator (sum(x_i - mean) ** 2) based on new received bounding boxes
        with Welford algorithm.
        Args: new_objects: a list of dictionaries. each dictionary has attributes of a detected object such as
        "id", "centroidReal" (a tuple of the centroid coordinates (cx,cy,w,h) of the box) and "bboxReal" (a tuple
        of the (xmin,ymin,xmax,ymax) coordinate of the box)
        """
        self.num_calls += 1
        for item in new_objects:
            cx, cy, w, h = [int(i) for i in item["centroidReal"]]
            cx = min(cx, self.img_width - 1)
            cy = min(cy, self.img_height - 1)
            self.count[cy, cx] += 1
            offset_old = [w, h] - self.mean[:, cy, cx]
            self.mean[:, cy, cx] += offset_old / self.count[cy, cx]
            offset_new = [w, h] - self.mean[:, cy, cx]
            self.m2[:, cy, cx] += offset_old * offset_new

    def compute_stats(self):
        """ calculate final mean, variance and standard deviation"""
        self.num_calls += 1
        self.mean = self.mean
        self.var = self.m2 / np.where(self.count != 0, self.count, 1.0)
        self.std = np.sqrt(self.var)
