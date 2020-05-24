#!/usr/bin/python3
import argparse
from multiprocessing import Process
from libs.config_engine import ConfigEngine
import libs.pubsub


def start_engine(config, video_path):
    from libs.core import Distancing as CvEngine
    engine = CvEngine(config)
    engine.process_video(video_path)


def start_web_gui(config):
    from ui.web_gui import WebGUI
    ui = WebGUI(config)
    ui.start()


def main(config):
    if isinstance(config, str):
        config = ConfigEngine(config)
    libs.pubsub.init_shared_resources()

    video_path = config.get_section_dict("App")["VideoPath"]
    process_engine = Process(target=start_engine, args=(config, video_path,))

    process_engine.start()
    start_web_gui(config)

    process_engine.terminate()
    process_engine.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
