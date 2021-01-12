from fastapi import APIRouter
from typing import Optional

from api.models.app import AppDTO
from api.utils import (extract_config, handle_response, update_config,
                       map_section_from_config, map_to_config_file_format)

app_router = APIRouter()


@app_router.get("", response_model=AppDTO)
def get_app_config():
    """
    Returns the app configuration of the processor
    """
    return map_section_from_config("App", extract_config())


@app_router.put("", response_model=AppDTO)
def update_app_config(app: AppDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the app configuration of the processor
    """
    config_dict = extract_config()
    app_dict = map_to_config_file_format(app)
    config_dict["App"] = app_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(app_dict, success)
    return map_section_from_config("App", extract_config())
