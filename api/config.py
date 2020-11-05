import logging

from fastapi import FastAPI
from typing import Optional

from .areas import map_area, map_to_area_file_format
from .cameras import map_camera, map_to_camera_file_format
from .models.config_keys import ConfigDTO
from .utils import (
    extract_config, handle_config_response, update_and_restart_config
)

logger = logging.getLogger(__name__)

config_api = FastAPI()


def map_to_config_file_format(config_dto):
    config_dict = dict()
    for count, camera in enumerate(config_dto.cameras):
        config_dict["Source_" + str(count)] = map_to_camera_file_format(camera)
    for count, area in enumerate(config_dto.areas):
        config_dict["Area_" + str(count)] = map_to_area_file_format(area)
    return config_dict


def map_config(config, options):
    cameras_name = [x for x in config.keys() if x.startswith("Source")]
    areas_name = [x for x in config.keys() if x.startswith("Area")]
    return {
        "host": config.get("API").get("Host"),
        "port": config.get("API").get("Port"),
        "cameras": [map_camera(x, config, options) for x in cameras_name],
        "areas": [map_area(x, config) for x in areas_name]
    }


@config_api.get("/", response_model=ConfigDTO)
async def get_config(options: Optional[str] = ""):
    logger.info("get-config requests on api")
    return map_config(extract_config(), options)


@config_api.put("/")
async def update_config(config: ConfigDTO):
    config_dict = map_to_config_file_format(config)

    success = update_and_restart_config(config_dict)
    return handle_config_response(config_dict, success)
