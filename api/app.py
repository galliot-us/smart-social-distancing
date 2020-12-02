from fastapi import APIRouter
from typing import Optional

from .models.app import AppDTO
from .utils import (extract_config, get_config, handle_response, update_config,
                    pascal_to_camel_case, camel_to_pascal_case)

app_router = APIRouter()


def map_app(config):
    app_section = config.get_section_dict("App")
    config_mapped = {}
    for key, value in app_section.items():
        config_mapped[pascal_to_camel_case(key)] = value
    return config_mapped


def map_to_app_file_format(app: AppDTO):
    app_dict = app.dict()
    app_file_dict = {}
    for key, value in app_dict.items():
        app_file_dict[camel_to_pascal_case(key)] = str(value)
    return app_file_dict


@app_router.get("", response_model=AppDTO)
def get_app_config():
    return map_app(get_config())


@app_router.put("", response_model=AppDTO)
def update_app_config(app: AppDTO, reboot_processor: Optional[bool] = True):
    config_dict = extract_config()
    app_dict = map_to_app_file_format(app)
    config_dict[f"App"] = app_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(app_dict, success)
