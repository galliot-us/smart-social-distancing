from utils import config_parser
from builders import builder

import torch
import pathlib


class Detector:
    def __init__(self, config):
        self.config = config
        self.cfg = config_parser.parse("configs/config.yaml")
        self.device = torch.device("cuda" if config.get_section_dict('Detector')['Gpu'] else "cpu")
        self._input_size = self.cfg.DATA_PRESET.IMAGE_SIZE
        self.load_model()
        self.detection_model = builder.build_detection_model(self.args)
        self.detection_model.load_model()
        self._aspect_ratio = float(self._input_size[1]) / self._input_size[0]
        self.hm_size = self.cfg.DATA_PRESET.HEATMAP_SIZE
        self.eval_joints = list(range(self.cfg.DATA_PRESET.NUM_JOINTS))

    def load_model(self):
        # TODO: add download checkpoint script
        model_file = pathlib.Path('/repo/data/x86/fast_res50_256x192.pth')
        if not model_file.exists():
            # TODO: add model link
            pass

        self.pose_model = builder.build_sppe_model(self.cfg.MODEL, preset_cfg=self.cfg.DATA_PRESET)
        print(f'Loading pose model from {model_file}...')
        self.pose_model.load_state_dict(torch.load(model_file, map_location=self.device))
        self.pose_model.to(self.device)
        self.pose_model.eval()
