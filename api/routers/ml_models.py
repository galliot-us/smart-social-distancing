import json
import os
from pathlib import Path


from fastapi import APIRouter, status, Body
from starlette.exceptions import HTTPException

from api.models.ml_model import MLModelDTO
from api.routers.cameras import validate_camera_existence
from api.settings import Settings
from api.utils import extract_config
from libs.utils.config import get_source_config_directory


ml_models_router = APIRouter()
settings = Settings()

# Todo: test if I create a new camera, if base path is created.

"""
def validate_variables_per_model(model_name, variables):
    if model_name == "openvino":
        pass


def validate_model_parameters(model_parameters):
    # Try to check this with ypydantic, accept one of several models
    is_valid = True
    if model_parameters.model_name == "openvino":
        image_size = model_parameters.variables["ImageSize"]
        model_path = model_parameters.variables["ModelPath"]
        class_id = model_parameters.variables["ClassID"]
        min_score = model_parameters.variables["MinScore"]
        if len(model_parameters.variables) != 4:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Extra parameters for submitted model")

    elif model_parameters.model_name == "openvino":
        pass

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Given parameters are incoherent. Check if"
                                                                        f"the model name corresponds with submitted "
                                                                        f"variables.")
"""

# TODO: PARA HACER AL FINAL.
#  VER QUE HAY CIERTOS PARAMETROS QUE SON GLOBALES COMO IMAGE SIZE. AVERIGUAR BIEN ESTO QUE SE PUEDE HACER. SI SE
#  TOMAN DEL JSON FILE O DEL CONFIG FILE.


def pascal_case_to_snake_case(variables):
    # TODO: hacer esta funcion que pase todas las keys de image_size to ImageSize
    pass


@ml_models_router.post("/{camera_id}/")
async def modify_ml_model(camera_id: str, model_parameters: MLModelDTO):
    validate_camera_existence(camera_id)
    # TODO: ES IMPORTANTISIMO QUE SE VALIDE QUE LOS DATOS SON PERFECTOS. SI NO DESPUES CUANDO LEVANTE DE NUEVO EL
    #  PROCESSOR, SE VA A LEER CUALQUEIR COSA Y NO SE VA A PODER PROCESAR LA CAMARA.

    #  TODO: QUE ONDA CON EL REBOOT PROCESOR? SE PODRIA APLICAR ACA? CAPAZ DA VENTAJA

    base_path = os.path.join(get_source_config_directory(settings.config), camera_id)
    models_directory_path = os.path.join(base_path, "ml_models")
    json_file_path = os.path.join(models_directory_path,
                                  f"model_{settings.config.get_section_dict('Detector')['Device']}.json")

    # variables = pascal_case_to_snake_case(model_parameters.variables)
    variables = model_parameters.variables  # Esta linea es temporal para que el endpoint funcione, debe eliminarse dsp.

    # Create .json file
    json_content = {
        "model_name": model_parameters.model_name,
        "variables": variables
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

    return {
        "Saborcito": "BIEN FALADO"
    }
