import json
import os
from pathlib import Path


from fastapi import APIRouter, status, Body
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.ml_model import MLModelDTO
from api.routers.cameras import validate_camera_existence
from api.settings import Settings
from api.utils import restart_processor, handle_response
from libs.utils.config import get_source_config_directory


ml_model_router = APIRouter()
settings = Settings()


def pascal_case_to_snake_case(parameters):
    result = {}

    for key, value in parameters:
        result[''.join(word.title() for word in key.split('_'))] = value

    if "ClassId" in result.keys():
        result["ClassID"] = result["ClassId"]
        del result["ClassId"]

    return result


@ml_model_router.post("/{camera_id}")
async def modify_ml_model(camera_id: str, model_parameters: MLModelDTO, reboot_processor: Optional[bool] = True):
    validate_camera_existence(camera_id)

    parameters = pascal_case_to_snake_case(model_parameters)

    base_path = os.path.join(get_source_config_directory(settings.config), camera_id)
    models_directory_path = os.path.join(base_path, "ml_models")
    json_file_path = os.path.join(models_directory_path, f"model_{parameters['Device']}.json")

    model_name = parameters["Name"]
    del parameters["Name"]
    del parameters["Device"]

    # Create or modify .json file
    json_content = {
        "model_name": model_name,
        "variables": parameters
    }

    if os.path.exists(json_file_path):
        with open(json_file_path, 'w') as outfile:
            json.dump(json_content, outfile)
    else:
        # Hypothesis: source config directory (base_path) should always exists.
        if not os.path.exists(models_directory_path):
            Path(models_directory_path).mkdir(parents=True, exist_ok=True)

        with open(json_file_path, 'x+') as outfile:
            json.dump(json_content, outfile)

    # Reboot processor if set
    success = True
    if reboot_processor:
        success = restart_processor()

    return handle_response(json_content, success, decamelize=False)
