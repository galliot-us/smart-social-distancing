from models.fastpose import FastPose
from detectors.yolo_wrapper import YoloWrapper
from easydict import EasyDict as edict

def build_sppe_model(cfg, preset_cfg):
    args = cfg.copy()
    default_args = {
        'PRESET': preset_cfg,
    }
    for name, value in default_args.items():
        args.setdefault(name, value)
    return FastPose(**args)


def build_detection_model(opt):
    cfg = edict()
    cfg.CONFIG = 'detectors/yolo/cfg/yolov3-spp.cfg'
    cfg.WEIGHTS = 'detectors/yolo/data/yolov3-spp.weights'
    cfg.INP_DIM = 608
    cfg.NMS_THRES = 0.6
    cfg.CONFIDENCE = 0.1
    cfg.NUM_CLASSES = 80
    return YoloWrapper(cfg, opt)
