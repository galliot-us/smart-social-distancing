import logging

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from .areas import map_area, map_to_area_file_format
from .cameras import map_camera, map_to_camera_file_format
from .models.config_keys import ConfigDTO
from .utils import (
    extract_config, handle_response, update_and_restart_config
)
from constants import PROCESSOR_VERSION

logger = logging.getLogger(__name__)

config_router = APIRouter()


class ConfigInfo(BaseModel):
    version: str
    device: str
    has_been_configured: bool

    class Config:
        schema_extra = {
            "example": {
                "version": PROCESSOR_VERSION,
                "device": "device",
                "has_been_configured": True
            }
        }


def map_to_config_file_format(config_dto: ConfigDTO):
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
        "cameras": [map_camera(x, config, options) for x in cameras_name],
        "areas": [map_area(x, config) for x in areas_name]
    }


def processor_info(config):
    has_been_configured = bool(config["App"]["HasBeenConfigured"])
    device = config["Detector"]["Device"]
    if config["Detector"]["Name"] == "openvino":
        device += "-openvino"
    return {
        "version": PROCESSOR_VERSION,
        "device": device,
        "has_been_configured": has_been_configured
    }


@config_router.get("", response_model=ConfigDTO)
async def get_config(options: Optional[str] = ""):
    """
    Returns the configuration used by the processor
    """
    logger.info("get-config requests on api")
    return map_config(extract_config(), options)


@config_router.put("", response_model=ConfigDTO)
async def update_config(config: ConfigDTO):
    """
    Overwrites the configuration used by the processor.
    """
    config_dict = map_to_config_file_format(config)
    success = update_and_restart_config(config_dict)
    return handle_response(config_dict, success)


@config_router.get("/info", response_model=ConfigInfo)
async def get_processor_info():
    """
    Returns basic info regarding this processor
    """
    return processor_info(extract_config())
