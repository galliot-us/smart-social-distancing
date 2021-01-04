from fastapi import APIRouter
from typing import Optional

from api.models.core import CoreDTO
from api.utils import (extract_config, handle_response, update_config,
                       map_section_from_config, map_to_config_file_format)

core_router = APIRouter()


@core_router.get("", response_model=CoreDTO)
def get_core_config():
    """
    Returns the core configuration of the processor
    """
    return map_section_from_config("CORE", extract_config())


@core_router.put("", response_model=CoreDTO)
def update_core_config(core: CoreDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the core configuration of the processor
    """
    config_dict = extract_config()
    core_dict = map_to_config_file_format(core)
    config_dict["CORE"] = core_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(core_dict, success)
    return map_section_from_config("CORE", extract_config())
