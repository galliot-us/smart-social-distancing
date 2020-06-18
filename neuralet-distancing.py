#!/usr/bin/python3
import os
import argparse
import logging
import sys
import threading

from multiprocessing import Process
from libs.config_engine import ConfigEngine


logger = logging.getLogger(__name__)


def start_cv_engine(config, video_path):
    try:
        if video_path:
            from libs.core import Distancing as CvEngine
            engine = CvEngine(config)
            engine.process_video(video_path)
        else:
            logger.error('"VideoPath" not set in .ini [App] section')
    except Exception:
        # this runs sys.excinfo() and logs the result
        logger.error("CvEngine failed.", exc_info=True)

def start_web_gui(config):
    from ui.web_gui import WebGUI
    ui = WebGUI(config)
    ui.start()

def main(config, verbose=False):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)
    video_path = config.get_section_dict("App").get("VideoPath", None)

    # create our inference process
    if os.path.isdir('/opt/nvidia/deepstream'):
        from libs.detectors.deepstream import GstEngine, DsConfig
        process_engine = GstEngine(DsConfig(config), debug=verbose)
    else:
        # DeepStream is not available. Let's try CvEngine
        process_engine = Process(target=start_cv_engine, args=(config, video_path,))

    # create our ui process
    process_api = Process(target=start_web_gui, args=(config,))

    # start both processes
    process_api.start()
    process_engine.start()
    logger.info("Services Started.")

    # wait forever
    forever = threading.Event()
    try:
        forever.wait()
    except KeyboardInterrupt:
        logger.info("Received interrupt. Terminating...")

    if hasattr(process_engine, 'stop'):
        # DsEngine shuts down by asking
        # GLib.MainLoop to quit. SIGTERM does this too,
        # but it wouldn't call some extra debug stuff
        # that's in GstEngine's quit()
        # (debug .dot file, .pdf if graphviz is available)
        # .stop() will call .terminate() if it times out.
        process_engine.stop()
        process_engine.join()
    else:
        process_engine.terminate()
        process_engine.join()

    logger.info("Inference Engine terminated.")
    process_api.terminate()
    process_api.join()
    logger.info("Web GUI terminated.")
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    sys.exit(main(args.config, args.verbose))
