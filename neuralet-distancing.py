#!/usr/bin/python3
import argparse
from multiprocessing import Process
import threading
from libs.config_engine import ConfigEngine
import libs.pubsub
import logging

logger = logging.getLogger(__name__)


def start_engine(config, video_path):
    if video_path:
        from libs.core import Distancing as CvEngine
        engine = CvEngine(config)
        engine.process_video(video_path)
    else:
        logger.info('Skipping CVEngine as video_path is not set')


def start_web_gui(config):
    from ui.web_gui import WebGUI
    ui = WebGUI(config)
    ui.start()


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)
    libs.pubsub.init_shared_resources()

    video_path = config.get_section_dict("App").get("VideoPath", None)
    process_engine = Process(target=start_engine, args=(config, video_path,))
    process_api = Process(target=start_web_gui, args=(config,))

    process_api.start()
    process_engine.start()
    logger.info("Services Started.")

    forever = threading.Event()
    try:
        forever.wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt. Terminating...")

    process_engine.terminate()
    process_engine.join()
    logger.info("CV Engine terminated.")
    process_api.terminate()
    process_api.join()
    logger.info("Web GUI terminated.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
