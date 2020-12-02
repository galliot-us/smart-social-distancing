from fastapi import APIRouter
from typing import Optional

from api.models.classifier import ClassifierDTO
from api.utils import (extract_config, get_config, handle_response, update_config,
                       pascal_to_camel_case, camel_to_pascal_case)

classifier_router = APIRouter()


def map_classifier(config):
    classifier_section = config.get_section_dict("Classifier")
    classifier_mapped = {}
    for key, value in classifier_section.items():
        classifier_mapped[pascal_to_camel_case(key)] = value
    return classifier_mapped


def map_to_classifier_file_format(classifier: ClassifierDTO):
    classifier_dicr = classifier.dict()
    classifier_file_dict = {}
    for key, value in classifier_dicr.items():
        classifier_file_dict[camel_to_pascal_case(key)] = str(value)
    return classifier_file_dict


@classifier_router.get("", response_model=ClassifierDTO)
<<<<<<< HEAD
def get_classifier_config():
=======
def get_core_config():
>>>>>>> 875f8ee... Create classifier endpoint.
    """
    Returns the classifier configuration of the processor
    """
    return map_classifier(get_config())


@classifier_router.put("", response_model=ClassifierDTO)
<<<<<<< HEAD
def update_classifier_config(classifier: ClassifierDTO, reboot_processor: Optional[bool] = True):
=======
def update_core_config(classifier: ClassifierDTO, reboot_processor: Optional[bool] = True):
>>>>>>> 875f8ee... Create classifier endpoint.
    """
    Updates the classifier configuration of the processor
    """
    config_dict = extract_config()
    classifier_dict = map_to_classifier_file_format(classifier)
    config_dict["Classifier"] = classifier_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(classifier_dict, success)
