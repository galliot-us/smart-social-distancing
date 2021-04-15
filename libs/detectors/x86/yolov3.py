from __future__ import division
import time
import torch
from torch.autograd import Variable
from libs.detectors.x86.yolov3_backbone.util import *
from libs.detectors.x86.yolov3_backbone.darknet import Darknet
import os
import wget
from libs.detectors.utils.fps_calculator import convert_infr_time_to_fps


class Detector:
    '''
    Perform object detection with yolov3 model. detect pedestrian's bounding boxes from given image.
    :param config: Is a ConfigEngine instance which provides necessary parameters.
    '''

    def __init__(self, config, model_name, variables):
        self.config = config
        self.model_name = model_name
        self.model_variables = variables
        self.fps = None
        self.w, self.h, _ = [int(i) for i in self.model_variables['ImageSize'].split(',')]
        assert self.w == self.h
        self.model_file = 'yolov3.weights'
        self.model_path = '/repo/data/x86/' + self.model_file

        # Get the model .weight file path from the config.
        # If there is no .weight file in the path it will be downloaded automatically from base_url
        user_model_path = self.model_variables['ModelPath']
        if len(user_model_path) > 0:
            print('using %s as model' % user_model_path)
            self.model_path = user_model_path
        else:
            url = 'https://github.com/neuralet/neuralet-models/blob/master/amd64/coco_yolo_v3/yolov3.weights?raw=true'

            if not os.path.isfile(self.model_path):
                print('model does not exist under: ', self.model_path, 'downloading from ', url)
                wget.download(url, self.model_path)

        self.nms_threshold = 0.5
        self.confidence = float(self.model_variables['MinScore'])

        self._num_classes = 80  # the model is trained on COCO dataset which includes 80 classes
        self._CUDA = torch.cuda.is_available()
        self._bbox_attrs = 5 + self._num_classes
        self._model = Darknet('libs/detectors/x86/yolov3_backbone/cfg/yolov3.cfg')
        self._model.load_weights(self.model_path)
        self._model.net_info["height"] = self.w  # resolution % 32 == 0
        self._inp_dim = int(self._model.net_info["height"])
        assert self._inp_dim % 32 == 0
        assert self._inp_dim > 32
        if self._CUDA:
            self._model.cuda()

        self._model.eval()

    @staticmethod
    def prep_image(img, inp_dim):
        """
        Prepare image for inputting to the neural network.

        Returns a Variable
        """

        orig_im = img
        dim = orig_im.shape[1], orig_im.shape[0]
        img = (letterbox_image(orig_im, (inp_dim, inp_dim)))
        img_ = img[:, :, ::-1].transpose((2, 0, 1)).copy()
        img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
        return img_, orig_im, dim

    def inference(self, resized_rgb_image):
        img, orig_im, dim = self.prep_image(resized_rgb_image, self._inp_dim)
        im_dim = torch.FloatTensor(dim).repeat(1, 2)

        if self._CUDA:
            im_dim = im_dim.cuda()
            img = img.cuda()

        # start calculate fps
        t_begin = time.perf_counter()
        with torch.no_grad():
            output = self._model(Variable(img), self._CUDA)
        output = write_results(output, self.confidence, self._num_classes, nms=True, nms_conf=self.nms_threshold)
        inference_time = time.perf_counter() - t_begin
        self.fps = convert_infr_time_to_fps(inference_time)

        im_dim = im_dim.repeat(output.size(0), 1)
        scaling_factor = torch.min(self._inp_dim / im_dim, 1)[0].view(-1, 1)
        output[:, [1, 3]] -= (self._inp_dim - scaling_factor * im_dim[:, 0].view(-1, 1)) / 2
        output[:, [2, 4]] -= (self._inp_dim - scaling_factor * im_dim[:, 1].view(-1, 1)) / 2
        output[:, 1:5] /= scaling_factor
        for i in range(output.shape[0]):
            output[i, [1, 3]] = torch.clamp(output[i, [1, 3]], 0.0, im_dim[i, 0])
            output[i, [2, 4]] = torch.clamp(output[i, [2, 4]], 0.0, im_dim[i, 1])

        result = []
        for i, pred in enumerate(output):
            c1 = pred[1:3].cpu().int().numpy()  # unormalized [xmin, ymin]
            c2 = pred[3:5].cpu().int().numpy()  # unormalized [xmax, ymax]
            cls = int(pred[-1].cpu())
            score = float(pred[5].cpu())
            if cls == 0:  # person class index is '0' at coco dataset
                bbox_dict = {"id": "1-" + str(i),
                             "bbox": [c1[1] / self.h, c1[0] / self.w, c2[1] / self.h, c2[0] / self.w], "score": score,
                             "face": None}
                result.append(bbox_dict)
        return result
