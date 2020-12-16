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


def build_detection_model(name, config):
    detector_name = name.split("_")[-1]
    if detector_name == "ssd":
        from libs.detectors.x86 import mobilenet_ssd
        detector = mobilenet_ssd.Detector(config=config)
    else:
        raise ValueError('Not supported detector named: ', name, ' for AlphaPose.')
    return detector
