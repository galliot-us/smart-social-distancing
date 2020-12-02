from fastapi import APIRouter
from typing import Optional

from api.models.tracker import TrackerDTO
from api.utils import (extract_config, get_config, handle_response, update_config,
                       pascal_to_camel_case, camel_to_pascal_case)

tracker_router = APIRouter()


def map_tracker(config):
    tracker_section = config.get_section_dict("Tracker")
    tracker_mapped = {}
    for key, value in tracker_section.items():
        tracker_mapped[pascal_to_camel_case(key)] = value
    return tracker_mapped


def map_to_tracker_file_format(tracker: TrackerDTO):
    tracker_dicr = tracker.dict()
    tracker_file_dict = {}
    for key, value in tracker_dicr.items():
        tracker_file_dict[camel_to_pascal_case(key)] = str(value)
    return tracker_file_dict


@tracker_router.get("", response_model=TrackerDTO)
def get_core_config():
    """
    Returns the tracker configuration of the processor
    """
    return map_tracker(get_config())


@tracker_router.put("", response_model=TrackerDTO)
def update_core_config(tracker: TrackerDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the tracker configuration of the processor
    """
    config_dict = extract_config()
    tracker_dict = map_to_tracker_file_format(tracker)
    config_dict["Tracker"] = tracker_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(tracker_dict, success)
