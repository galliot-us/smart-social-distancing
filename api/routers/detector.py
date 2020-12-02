from fastapi import APIRouter
from typing import Optional

from api.models.detector import DetectorDTO
from api.utils import (extract_config, get_config, handle_response, update_config,
                       pascal_to_camel_case, camel_to_pascal_case)

detector_router = APIRouter()


def map_detector(config):
    detector_section = config.get_section_dict("Detector")
    detector_mapped = {}
    for key, value in detector_section.items():
        detector_mapped[pascal_to_camel_case(key)] = value
    return detector_mapped


def map_to_detector_file_format(detector: DetectorDTO):
    detector_dicr = detector.dict()
    detector_file_dict = {}
    for key, value in detector_dicr.items():
        detector_file_dict[camel_to_pascal_case(key)] = str(value)
    return detector_file_dict


@detector_router.get("", response_model=DetectorDTO)
def get_core_config():
    """
    Returns the detector configuration of the processor
    """
    return map_detector(get_config())


@detector_router.put("", response_model=DetectorDTO)
def update_core_config(detector: DetectorDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the detector configuration of the processor
    """
    config_dict = extract_config()
    detector_dict = map_to_detector_file_format(detector)
    config_dict["Detector"] = detector_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(detector_dict, success)
