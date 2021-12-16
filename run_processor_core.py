#!/usr/bin/python3
import argparse
from libs.config_engine import ConfigEngine
import logging

logger = logging.getLogger(__name__)


def start_core(config):
    from libs.processor_core import ProcessorCore
    core = ProcessorCore(config)

    logger.info("Core Started.")
    core.start()
    logger.info("Core Terminated.")


def main(config):
    logging.basicConfig(level=logging.INFO)
    if isinstance(config, str):
        config = ConfigEngine(config)

    start_core(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    main(args.config)
