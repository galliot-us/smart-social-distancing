from fastapi import APIRouter
from typing import Optional

from api.models.classifier import ClassifierDTO
from api.utils import (
    extract_config, handle_response, update_config, map_section_from_config,
    map_to_config_file_format)

classifier_router = APIRouter()


@classifier_router.get("", response_model=ClassifierDTO)
def get_classifier_config():
    """
    Returns the classifier configuration of the processor
    """
    return map_section_from_config("Classifier", extract_config())


@classifier_router.put("", response_model=ClassifierDTO)
def update_classifier_config(classifier: ClassifierDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the classifier configuration of the processor
    """
    config_dict = extract_config()
    classifier_dict = map_to_config_file_format(classifier)
    config_dict["Classifier"] = classifier_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(classifier_dict, success)
    return map_section_from_config("Classifier", extract_config())
