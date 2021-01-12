from fastapi import APIRouter
from typing import Optional

from api.models.detector import DetectorDTO
from api.utils import (extract_config, handle_response, update_config,
                       map_section_from_config, map_to_config_file_format)

detector_router = APIRouter()


@detector_router.get("", response_model=DetectorDTO)
def get_detector_config():
    """
    Returns the detector configuration of the processor
    """
    return map_section_from_config("Detector", extract_config())


@detector_router.put("", response_model=DetectorDTO)
def update_detector_config(detector: DetectorDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the detector configuration of the processor
    """
    config_dict = extract_config()
    detector_dict = map_to_config_file_format(detector)
    config_dict["Detector"] = detector_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(detector_dict, success)
    return map_section_from_config("Detector", extract_config())
