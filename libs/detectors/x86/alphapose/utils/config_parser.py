import yaml
from easydict import EasyDict as edict

def parse(config_file):
    with open(config_file) as f:
        config = edict(yaml.load(f, Loader=yaml.FullLoader))
        return config