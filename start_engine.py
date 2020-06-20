#!/usr/bin/python3
import argparse
from multiprocessing import Process
import threading
from libs.config_engine import ConfigEngine
import logging

logger = logging.getLogger(__name__)


def start_engine(config, video_path):
    logger.info("Engine Started.")
    
    if video_path:
        from libs.core import Distancing as CvEngine
        engine = CvEngine(config)
        engine.process_video(video_path)
    else:
        logger.error('video_path is not set in config file')
    
    logger.info("Engine terminated.")


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)

    video_path = config.get_section_dict("App").get("VideoPath", None)
    start_engine(config, video_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
