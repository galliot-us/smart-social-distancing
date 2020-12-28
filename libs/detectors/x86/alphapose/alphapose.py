import sys

sys.path.append("libs/detectors/x86/alphapose")
from utils import config_parser
from builders import builder
from utils.bbox import box_to_center_scale, center_scale_to_box
from utils.pose_nms import pose_nms
from utils.transformations import get_affine_transform, transform_preds, im_to_torch, get_max_pred
from convert_results_format import prepare_detection_results, prepare_poses_results

import torch
import cv2
import numpy as np
import pathlib
import time
from libs.detectors.utils.fps_calculator import convert_infr_time_to_fps

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Detector:
    """
       Perform object detection with the AlphaPose model.
       original repository of the model: https://github.com/MVIG-SJTU/AlphaPose

       :param config: Is a ConfigEngine instance which provides necessary parameters.
       """
    def __init__(self, config):
        self.config = config
        self.name = config.get_section_dict('Detector')['Name']
        self.w, self.h, _ = [int(i) for i in self.config.get_section_dict('Detector')['ImageSize'].split(',')]
        self.cfg = config_parser.parse("libs/detectors/x86/alphapose/configs/config.yaml")
        self.device = torch.device("cuda" if config.get_section_dict('Detector')['Device'].endswith("gpu") else "cpu")
        self._input_size = self.cfg.DATA_PRESET.IMAGE_SIZE
        self.load_model()
        self.detection_model = builder.build_detection_model(self.name, config)
        self._aspect_ratio = float(self._input_size[1]) / self._input_size[0]
        self.hm_size = self.cfg.DATA_PRESET.HEATMAP_SIZE
        self.eval_joints = list(range(self.cfg.DATA_PRESET.NUM_JOINTS))
        self.fps = None

    def load_model(self):
        model_file = pathlib.Path('/repo/data/x86/fast_res50_256x192.pth')
        if not model_file.exists():
            import gdown
            logger.info("did not find model's checkpoint file, start downloading ...")
            url = 'https://drive.google.com/uc?id=1kQhnMRURFiy7NsdS8EFL-8vtqEXOgECn'
            output = '/repo/data/x86/fast_res50_256x192.pth'
            gdown.download(url, output, quiet=False)

        self.pose_model = builder.build_sppe_model(self.cfg.MODEL, preset_cfg=self.cfg.DATA_PRESET)
        print(f'Loading pose model from {model_file}...')
        self.pose_model.load_state_dict(torch.load(model_file, map_location=self.device))
        self.pose_model.to(self.device)
        self.pose_model.eval()

    def inference(self, image):
        """
            inference function sets input tensor to input image and gets the output.
            The model provides corresponding detection output which is used for creating result
            Args:
                resized_rgb_image: uint8 numpy array with shape (img_height, img_width, channels)

            Returns:
                result: a dictionary contains of [{"id": 0, "bbox": [y1, x1, y2, x2], "score":s%, "face": [y1, x1, y2, x2]}, {...}, {...}, ...]
        """
        t_begin = time.perf_counter()
        detections = self.detection_model.inference(image)
        if len(detections) == 0:
            return []
        detections = prepare_detection_results(detections, self.w, self.h)
        with torch.no_grad():
            inps, cropped_boxes, boxes, scores, ids = self._transform_detections(image, detections)
            inps = inps.to(self.device)
            hm = self.pose_model(inps)
            poses = self._post_process(hm, cropped_boxes, boxes, scores, ids)
        inference_time = time.perf_counter() - t_begin
        self.fps = convert_infr_time_to_fps(inference_time)
        results = prepare_poses_results(poses, self.w, self.h, scores)
        return results

    def _transform_detections(self, image, dets):
        if isinstance(dets, int):
            return 0, 0
        dets = dets[dets[:, 0] == 0]
        boxes = dets[:, 1:5]
        scores = dets[:, 5:6]
        ids = torch.zeros(scores.shape)
        inps = torch.zeros(boxes.size(0), 3, *self._input_size)
        cropped_boxes = torch.zeros(boxes.size(0), 4)
        for i, box in enumerate(boxes):
            inps[i], cropped_box = self._transform_single_detection(image, box)
            cropped_boxes[i] = torch.FloatTensor(cropped_box)
        return inps, cropped_boxes, boxes, scores, ids

    def _transform_single_detection(self, image, bbox):
        xmin, ymin, xmax, ymax = bbox
        center, scale = box_to_center_scale(
            xmin, ymin, xmax - xmin, ymax - ymin, self._aspect_ratio)
        scale = scale * 1.0

        input_size = self._input_size
        inp_h, inp_w = input_size

        trans = get_affine_transform(center, scale, 0, [inp_w, inp_h])
        inp_h, inp_w = self._input_size
        img = cv2.warpAffine(image, trans, (int(inp_w), int(inp_h)), flags=cv2.INTER_LINEAR)
        bbox = center_scale_to_box(center, scale)

        img = im_to_torch(img)
        img[0].add_(-0.406)
        img[1].add_(-0.457)
        img[2].add_(-0.480)

        return img, bbox

    def _post_process(self, hm, cropped_boxes, boxes, scores, ids):
        assert hm.dim() == 4
        pose_coords = []
        pose_scores = []
        for i in range(hm.shape[0]):
            bbox = cropped_boxes[i].tolist()
            pose_coord, pose_score = self._heatmap_to_coord(hm[i][self.eval_joints], bbox, hm_shape=self.hm_size,
                                                           norm_type=None)
            pose_coords.append(torch.from_numpy(pose_coord).unsqueeze(0))
            pose_scores.append(torch.from_numpy(pose_score).unsqueeze(0))

        preds_img = torch.cat(pose_coords)
        preds_scores = torch.cat(pose_scores)

        boxes, scores, ids, preds_img, preds_scores, pick_ids = \
            pose_nms(boxes, scores, ids, preds_img, preds_scores, 0)

        _result = []
        for k in range(len(scores)):
            _result.append(
                {
                    'keypoints': preds_img[k],
                    'kp_score': preds_scores[k],
                    'proposal_score': torch.mean(preds_scores[k]) + scores[k] + 1.25 * max(preds_scores[k]),
                    'idx': ids[k],
                    'bbox': [boxes[k][0], boxes[k][1], boxes[k][2], boxes[k][3]]
                }
            )
        return _result

    def _heatmap_to_coord(self, hms, bbox, hms_flip=None, **kwargs):
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
            preds[i] = transform_preds(coords[i], center, scale,
                                       [hm_w, hm_h])

        return preds, maxvals
