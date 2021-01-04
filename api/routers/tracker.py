from fastapi import APIRouter
from typing import Optional

from api.models.tracker import TrackerDTO
from api.utils import (extract_config, handle_response, update_config,
                       map_section_from_config, map_to_config_file_format)

tracker_router = APIRouter()


@tracker_router.get("", response_model=TrackerDTO)
def get_tracker_config():
    """
    Returns the tracker configuration of the processor
    """
    return map_section_from_config("Tracker", extract_config())


@tracker_router.put("", response_model=TrackerDTO)
def update_tracker_config(tracker: TrackerDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the tracker configuration of the processor
    """
    config_dict = extract_config()
    tracker_dict = map_to_config_file_format(tracker)
    config_dict["Tracker"] = tracker_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(tracker_dict, success)
    return map_section_from_config("Tracker", extract_config())
