import logging
import humps
import os
import shutil

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from share.commands import Commands

from .settings import Settings

logger = logging.getLogger(__name__)


def get_config():
    return Settings().config


def extract_config(config_type="all"):
    sections = get_config().get_sections()
    if config_type == "cameras":
        sections = [x for x in sections if x.startswith("Source_")]
    elif config_type == "areas":
        sections = [x for x in sections if x.startswith("Area_")]
    elif config_type == "source_post_processors":
        sections = [x for x in sections if x.startswith("SourcePostProcessor_")]
    elif config_type == "source_loggers":
        sections = [x for x in sections if x.startswith("SourceLogger_")]
    elif config_type == "area_loggers":
        sections = [x for x in sections if x.startswith("AreaLogger_")]
    elif config_type == "periodic_tasks":
        sections = [x for x in sections if x.startswith("PeriodicTask_")]
    config = {}

    for section in sections:
        config[section] = get_config().get_section_dict(section)
    return config


def restart_processor():
    from .queue_manager import QueueManager
    logger.info("Restarting video processor...")
    queue_manager = QueueManager()
    queue_manager.cmd_queue.put(Commands.STOP_PROCESS_VIDEO)
    stopped = queue_manager.result_queue.get()
    if stopped:
        queue_manager.cmd_queue.put(Commands.PROCESS_VIDEO_CFG)
        started = queue_manager.result_queue.get()
        if not started:
            logger.info("Failed to restart video processor...")
            return False
    return True


def update_config(config_dict, reboot_processor):
    logger.info("Updating config...")
    get_config().update_config(config_dict)
    get_config().reload()

    if reboot_processor:
        success = restart_processor()
        return success
    return True


def handle_response(response, success, status_code=status.HTTP_200_OK):
    if not success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=jsonable_encoder({
                "msg": "Failed to restart video processor",
                "type": "unknown error on the config file",
                "body": humps.decamelize(response)
            })
        )
    content = humps.decamelize(response) if response else None
    return JSONResponse(status_code=status_code, content=content)


def reestructure_areas(config_dict):
    """Ensure that all [Area_0, Area_1, ...] are consecutive"""
    area_names = [x for x in config_dict.keys() if x.startswith("Area")]
    area_names.sort()
    for index, area_name in enumerate(area_names):
        if f"Area_{index}" != area_name:
            config_dict[f"Area_{index}"] = config_dict[area_name]
            config_dict.pop(area_name)
    return config_dict


def clean_up_file(filename):
    if os.path.exists(filename):
        if os.path.isdir(filename):
            shutil.rmtree(filename, ignore_errors=True)
        else:
            os.remove(filename)
    else:
        logger.info("The file does not exist")

    logger.info(f'Clean up of {filename} complete')


def pascal_to_camel_case(pascal_case_string: str) -> str:
    return pascal_case_string[0].lower() + pascal_case_string[1:]


def camel_to_pascal_case(pascal_case_string: str) -> str:
    return pascal_case_string[0].upper() + pascal_case_string[1:]
