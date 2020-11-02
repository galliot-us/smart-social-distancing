#!/usr/bin/python3
import argparse
from api.settings import Settings
from libs.config_engine import ConfigEngine

import logging

logger = logging.getLogger(__name__)


def start_api(config):
    from api.processor_api import ProcessorAPI
    api = ProcessorAPI()
    logger.info("API Started.")
    api.start()
    logger.info("API Terminated.")


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)
    Settings(config=config)
    start_api(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
