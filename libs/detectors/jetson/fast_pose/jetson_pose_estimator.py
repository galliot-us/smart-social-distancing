import cv2 as cv
import numpy as np
import logging
import os
import pycuda.driver as cuda
import pycuda.autoinit
import tensorrt as trt
import time

from libs.detectors.jetson.mobilenet_ssd_v2 import Detector 
from libs.detectors.jetson.fast_pose.tools.bbox import box_to_center_scale, center_scale_to_box
from libs.detectors.jetson.fast_pose.tools.convert_results_format import prepare_detection_results
from libs.detectors.jetson.fast_pose.tools.pose_nms import pose_nms
from libs.detectors.jetson.fast_pose.tools.transformations import im_to_tensor, get_affine_transform, get_max_pred


class TRTPoseEstimator:
    """
    Perform object detection with the given prebuilt tensorrt engine.

    :param config: Is a ConfigEngine instance which provides necessary parameters.
    :param output_layout:
    :model_name: Name of the ML model.
    :variables: A dict with all the variables needed for the ML model.
    """
    def __init__(self, config, model_name, variables,
                 detector_input_size=(300, 300),
                 pose_input_size=(256, 192),
                 heatmap_size=(64, 48),
                 batch_size=2, # TODO: 8? 1?
                 ):
        
        self.config = config
        self.model_name = model_name
        self.model_variables = variables

        self.class_id = int(self.model_variables['ClassID'])
        self.detector_thresh = self.model_variables['MinScore']
        # self.conf_threshold = self.model_variables['MinScore']

        self.detector_height, self.detector_width = detector_input_size
        self.pose_input_size = pose_input_size
        self.heatmap_size = heatmap_size
        self.batch_size = batch_size

        self.trt_logger = trt.Logger(trt.Logger.INFO)
        self.trt_runtime = trt.Runtime(self.trt_logger)

        self.host_inputs = None
        self.cuda_inputs = None
        self.host_outputs = None
        self.cuda_outputs = None
        self.stream = None
        self.raw_frame = None
        self.fps = None

        self.model = None
        self.detector = None
        self.load_model()

    def load_model(self):
        self.detector = Detector(self.config, "ssd_mobilenet_v2_coco", self.model_variables)
        self._init_cuda_stuff()

    def _batch_execute(self, context, num_detected_objects, batch_inps):
        cuda.memcpy_htod_async(self.cuda_inputs, self.host_inputs, self.stream)
        context.execute(batch_size=self.batch_size, bindings=[int(self.cuda_inputs), int(self.cuda_outputs)])
        cuda.memcpy_dtoh_async(self.host_outputs, self.cuda_outputs, self.stream)
        result_raw = self.host_outputs.reshape((self.batch_size, 64, 48, 17))  # TODO: it only works for fastpost
        # result = result_raw[0:num_detected_objects,:]
        return result_raw

    def inference(self, preprocessed_image): 
        raw_detections = self.detector.inference(preprocessed_image)
        detections = prepare_detection_results(raw_detections, self.detector_width, self.detector_height)

        resized_pose_img = cv.resize(self.raw_frame, (self.detector_width, self.detector_height))
        rgb_resized_img = cv.cvtColor(resized_pose_img, cv.COLOR_BGR2RGB)

        inps, cropped_boxes, boxes, scores, ids = self.transform_detections(rgb_resized_img, detections)
        if inps.shape[0] == 0:
            return (None, None, None, None, None)
        num_detected_objects = np.shape(inps)[0]
        batch_inps = np.zeros([self.batch_size, self.pose_input_size[0], self.pose_input_size[1], 3])
        result = np.zeros([num_detected_objects, 64, 48, 17])
        if num_detected_objects < self.batch_size:
            batch_inps[0:num_detected_objects, :] = inps
            self._load_images_to_buffer(batch_inps)
            with self.model.create_execution_context() as context:
                # Transfer input data to the GPU.
                result_raw = self._batch_execute(context, num_detected_objects, batch_inps)
                result = result_raw[0:num_detected_objects, :]

        else:
            remainder = num_detected_objects
            start_idx = 0
            while remainder > 0:
                endidx = min(self.batch_size, remainder)
                batch_inps[0:endidx, :] = inps[start_idx: start_idx + endidx, :]
                self._load_images_to_buffer(batch_inps)
                with self.model.create_execution_context() as context:
                    result_raw = self._batch_execute(context, num_detected_objects, batch_inps)
                    result[start_idx: start_idx + endidx, :] = result_raw[0:endidx, :]
                remainder -= self.batch_size
                start_idx += self.batch_size
        return (result, cropped_boxes, boxes, scores, ids)

    def preprocess(self, raw_image):
        self.raw_frame = raw_image
        return self.detector.preprocess(raw_image)

    def post_process(self, hm, cropped_boxes, boxes, scores, ids):
        if hm is None:
            return

        assert hm.ndim == 4
        pose_coords = []
        pose_scores = []
        for i in range(hm.shape[0]):
            hm_size = self.heatmap_size
            eval_joints = list(range(17))
            bbox = cropped_boxes[i].tolist()
            pose_coord, pose_score = self.heatmap_to_coord(hm[i, :, :, eval_joints], bbox, hm_shape=hm_size,
                                                           norm_type=None)

            pose_coords.append(pose_coord)
            pose_scores.append(pose_score)

        preds_img = np.array(pose_coords)
        preds_scores = np.array(pose_scores)
        boxes, scores, ids, preds_img, preds_scores, pick_ids = \
            pose_nms(boxes, scores, ids, preds_img, preds_scores, 0)
        _result = []
        for k in range(len(scores)):
            if np.ndim(preds_scores[k] == 2):
                preds_scores[k] = preds_scores[k][:, 0].reshape([17, 1])
                _result.append(
                    {
                        'keypoints': preds_img[k],
                        'kp_score': preds_scores[k],
                        'proposal_score': np.mean(preds_scores[k]) + scores[k] + 1.25 * max(preds_scores[k]),
                        'idx': ids[k],
                        'bbox': [boxes[k][0], boxes[k][1], boxes[k][2], boxes[k][3]]
                    }
                )
        return _result

    def transform_detections(self, image, dets):
        # image = image.transpose(2,1,0)
        input_size = self.pose_input_size
        if isinstance(dets, int):
            return 0, 0
        dets = dets[dets[:, 0] == 0]
        boxes = dets[:, 1:5]
        scores = dets[:, 5:6]
        ids = np.zeros(scores.shape)
        inps = np.zeros([boxes.shape[0], int(input_size[0]), int(input_size[1]), 3])
        cropped_boxes = np.zeros([boxes.shape[0], 4])
        for i, box in enumerate(boxes):

            inps[i], cropped_box = self.transform_single_detection(image, box, input_size)
            cropped_boxes[i] = np.float32(cropped_box)
        # inps = im_to_tensor(inps)
        return inps, cropped_boxes, boxes, scores, ids

    @staticmethod
    def transform_single_detection(image, bbox, input_size):
        aspect_ratio = input_size[1] / input_size[0]
        xmin, ymin, xmax, ymax = bbox
        center, scale = box_to_center_scale(
            xmin, ymin, xmax - xmin, ymax - ymin, aspect_ratio)
        scale = scale * 1.0

        input_size = input_size
        inp_h, inp_w = input_size

        trans = get_affine_transform(center, scale, 0, [inp_w, inp_h])
        inp_h, inp_w = input_size
        img = cv.warpAffine(image, trans, (int(inp_w), int(inp_h)), flags=cv.INTER_LINEAR)
        bbox = center_scale_to_box(center, scale)
        img = img / 255.0
        img[..., 0] = img[..., 0] - 0.406
        img[..., 1] = img[..., 1] - 0.457
        img[..., 2] = img[..., 2] - 0.480
        # img = im_to_tensor(img)
        return img, bbox

    def heatmap_to_coord(self, hms, bbox, hms_flip=None, **kwargs):
        if hms_flip is not None:
            hms = (hms + hms_flip) / 2
        if not isinstance(hms, np.ndarray):
            hms = hms.cpu().data.numpy()
        coords, maxvals = get_max_pred(hms)

        hm_h = hms.shape[1]
        hm_w = hms.shape[2]

        # post-processing
        for p in range(coords.shape[0]):
            hm = hms[p]
            px = int(round(float(coords[p][0])))
            py = int(round(float(coords[p][1])))
            if 1 < px < hm_w - 1 and 1 < py < hm_h - 1:
                diff = np.array((hm[py][px + 1] - hm[py][px - 1],
                                 hm[py + 1][px] - hm[py - 1][px]))
                coords[p] += np.sign(diff) * .25

        preds = np.zeros_like(coords)

        # transform bbox to scale
        xmin, ymin, xmax, ymax = bbox
        w = xmax - xmin
        h = ymax - ymin
        center = np.array([xmin + w * 0.5, ymin + h * 0.5])
        scale = np.array([w, h])
        # Transform back
        for i in range(coords.shape[0]):
            preds[i] = self.transform_preds(coords[i], center, scale,
                                            [hm_w, hm_h])

        return preds, maxvals

    def transform_preds(self, coords, center, scale, output_size):
        target_coords = np.zeros(coords.shape)
        trans = get_affine_transform(center, scale, 0, output_size, inv=1)
        target_coords[0:2] = self.affine_transform(coords[0:2], trans)
        return target_coords

    @staticmethod
    def affine_transform(pt, t):
        new_pt = np.array([pt[0], pt[1], 1.]).T
        new_pt = np.dot(t, new_pt)
        return new_pt[:2]

    def _load_images_to_buffer(self, img):
        preprocessed = np.asarray(img).ravel()
        np.copyto(self.host_inputs, preprocessed)

    def _load_engine(self):
        root_dir = "/repo"
        pose_model_file = f"TRT_{self.model_name}_fp_16_b{self.batch_size}.trt"
        pose_model_dir = f'{self.root_dir}/data/jetson/'
        self.pose_model_path = f'{pose_model_dir}{pose_model_file}'
        if not os.path.isfile(pose_model_path):
            exporters_dir = f"{root_dir}/exporters/jetson/"
            logging.info('model does not exist under: {}'.format(str(model_path)))
            logging.info("Creating model using pretrained weights")
            logger.info('model does not exist under: {}, downloading from {}'.format(str(model_path), base_url + model_file))
            os.makedirs(base_model_dir, exist_ok=True)
            base_url = "https://media.githubusercontent.com/media/neuralet/models/master/ONNX/fastpose/fastpose_resnet50_256_192_tf.onnx"
            os.system(f"bash {exporters_dir}generate_pose_tensorrt.bash {base_url} fp16 {self.batch_size}")
        else:
            with open(model_path, 'rb') as f:
                engine_data = f.read()
            engine = self.trt_runtime.deserialize_cuda_engine(engine_data)
        return engine

    def _init_cuda_stuff(self):
        self.model = self._load_engine()
        self.host_inputs, self.cuda_inputs, self.host_outputs, self.cuda_outputs, self.stream = self._allocate_buffers(self.model,
                                                                                                      self.batch_size,
                                                                                                      trt.float32)

    @staticmethod
    def _allocate_buffers(engine, batch_size, data_type):
        """
        This is the function to allocate buffers for input and output in the device
        Args:
           engine : The path to the TensorRT engine.
           batch_size : The batch size for execution time.
           data_type: The type of the data for input and output, for example trt.float32.

        Output:
           host_inputs_1: Input in the host.
           cuda_inputs_1: Input in the device.
           h_output_1: Output in the host.
           cuda_outputs_1: Output in the device.
           stream: CUDA stream.

        """
        # Determine dimensions and create page-locked memory buffers (which won't be swapped to disk) to hold host inputs/outputs.
        host_inputs_1 = cuda.pagelocked_empty(batch_size * trt.volume(engine.get_binding_shape(0)),
                                          dtype=trt.nptype(data_type))
        h_output = cuda.pagelocked_empty(batch_size * trt.volume(engine.get_binding_shape(1)),
                                         dtype=trt.nptype(data_type))
        # Allocate device memory for inputs and outputs.
        cuda_inputs_1 = cuda.mem_alloc(host_inputs_1.nbytes)

        cuda_outputs = cuda.mem_alloc(h_output.nbytes)
        # Create a stream in which to copy inputs/outputs and run inference.
        stream = cuda.Stream()
        return host_inputs_1, cuda_inputs_1, h_output, cuda_outputs, stream
