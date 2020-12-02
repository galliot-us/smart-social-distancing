from fastapi import APIRouter
from typing import Optional

from api.models.core import CoreDTO
from api.utils import (extract_config, get_config, handle_response, update_config,
                       pascal_to_camel_case, camel_to_pascal_case)

core_router = APIRouter()


def map_core(config):
    core_section = config.get_section_dict("CORE")
    config_mapped = {}
    for key, value in core_section.items():
        config_mapped[pascal_to_camel_case(key)] = value
    return config_mapped


def map_to_core_file_format(app: CoreDTO):
    app_dict = app.dict()
    app_file_dict = {}
    for key, value in app_dict.items():
        app_file_dict[camel_to_pascal_case(key)] = str(value)
    return app_file_dict


@core_router.get("", response_model=CoreDTO)
def get_core_config():
    """
    Returns the core configuration of the processor
    """
    return map_core(get_config())


@core_router.put("", response_model=CoreDTO)
def update_core_config(core: CoreDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the core configuration of the processor
    """
    config_dict = extract_config()
    core_dict = map_to_core_file_format(core)
    config_dict["CORE"] = core_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(core_dict, success)
