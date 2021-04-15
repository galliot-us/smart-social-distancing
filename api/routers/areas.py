import logging
import os
import re
import shutil
import json
from pathlib import Path

from fastapi import APIRouter, status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.area import AreaConfigDTO, AreasListDTO
from constants import ALL_AREAS
from .cameras import map_camera, get_cameras
from api.models.occupancy_rule import OccupancyRuleListDTO
from libs.utils import config as config_utils
from api.utils import (
    extract_config, get_config, handle_response, reestructure_areas, update_config, map_section_from_config,
    map_to_config_file_format, bad_request_serializer
)

areas_router = APIRouter()


def get_areas():
    config = extract_config(config_type="areas")
    return [map_section_from_config(x, config) for x in config.keys()]


@areas_router.get("", response_model=AreasListDTO)
async def list_areas():
    """
    Returns the list of areas managed by the processor.
    """
    return {
        "areas": get_areas()
    }


def area_all_data():
    config = get_config()
    area_all = config.get_area_all()

    if area_all is None:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=f"The area: 'ALL' does not exist")

    return {
        "violation_threshold": area_all.violation_threshold,
        "notify_every_minutes": area_all.notify_every_minutes,
        "emails": ",".join(area_all.emails),
        "enable_slack_notifications": area_all.enable_slack_notifications,
        "daily_report": area_all.daily_report,
        "daily_report_time": area_all.daily_report_time,
        "occupancy_threshold": area_all.occupancy_threshold,
        "id": area_all.id,
        "name": area_all.name,
        "cameras": ",".join(area_all.cameras)
    }


@areas_router.get("/{area_id}", response_model=AreaConfigDTO)
async def get_area(area_id: str):
    """
    Returns the configuration related to the area <area_id>
    """
    if area_id.upper() == ALL_AREAS:
        area = area_all_data()
    else:
        area = next((area for area in get_areas() if area["id"] == area_id), None)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")
    area["occupancy_rules"] = get_area_occupancy_rules(area["id"])
    return area


@areas_router.post("", response_model=AreaConfigDTO, status_code=status.HTTP_201_CREATED)
async def create_area(new_area: AreaConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a new area to the processor.
    """
    # TODO: We have to autogenerate the ID.
    config = get_config()
    areas = config.get_areas()
    if new_area.id in [area.id for area in areas]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Area already exists", error_type="config duplicated area")
        )
    elif new_area.id.upper() == ALL_AREAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Area with ID: 'ALL' is not valid.", error_type="Invalid ID")
        )

    cameras = config.get_video_sources()
    camera_ids = [camera.id for camera in cameras]
    if not all(x in camera_ids for x in new_area.cameras.split(",")):
        non_existent_cameras = set(new_area.cameras.split(",")) - set(camera_ids)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The cameras: {non_existent_cameras} do not exist")
    occupancy_rules = new_area.occupancy_rules
    del new_area.occupancy_rules
    area_dict = map_to_config_file_format(new_area)

    config_dict = extract_config()
    config_dict[f"Area_{len(areas)-1}"] = area_dict
    success = update_config(config_dict, reboot_processor)

    if occupancy_rules:
        set_occupancy_rules(new_area.id, occupancy_rules)

    if not success:
        return handle_response(area_dict, success, status.HTTP_201_CREATED)

    area_directory = os.path.join(os.getenv("AreaLogDirectory"), new_area.id, "occupancy_log")
    Path(area_directory).mkdir(parents=True, exist_ok=True)
    area_config_directory = os.path.join(os.getenv("AreaConfigDirectory"), new_area.id)
    Path(area_config_directory).mkdir(parents=True, exist_ok=True)

    # known issue: Occupancy rules not returned
    return next((area for area in get_areas() if area["id"] == area_dict["Id"]), None)


def modify_area_all(area_information):
    """
    Edits the configuration related to the area "ALL", an area that contains all cameras.
    """
    config = get_config()
    config_path = config.get_area_config_path(ALL_AREAS)

    json_content = {
        "global_area_all": {
            "ViolationThreshold": area_information.violationThreshold,
            "NotifyEveryMinutes": area_information.notifyEveryMinutes,
            "Emails": area_information.emails,
            "EnableSlackNotifications": area_information.enableSlackNotifications,
            "DailyReport": area_information.dailyReport,
            "DailyReportTime": area_information.dailyReportTime,
            "OccupancyThreshold": area_information.occupancyThreshold,
            "Id": ALL_AREAS,
            "Name": ALL_AREAS,
        }
    }

    if not os.path.exists(config_path):
        # Create the file with if necessary
        with open(config_path, 'x') as outfile:
            json.dump({"global_area_all": {}}, outfile)

    with open(config_path, "r") as file:
        file_content = json.load(file)

    file_content["global_area_all"] = json_content["global_area_all"]

    with open(config_path, "w") as file:
        json.dump(file_content, file)

    area_all = config.get_area_all()
    json_content["global_area_all"]["Cameras"] = ",".join(area_all.cameras)

    return {re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower(): value for key, value in json_content["global_area_all"].items()}


@areas_router.put("/{area_id}", response_model=AreaConfigDTO)
async def edit_area(area_id: str, edited_area: AreaConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the area <area_id>
    """
    if area_id.upper() == ALL_AREAS:
        area = modify_area_all(edited_area)
        if edited_area.occupancy_rules:
            set_occupancy_rules(ALL_AREAS, edited_area.occupancy_rules)
        else:
            delete_area_occupancy_rules(ALL_AREAS)
        area["occupancy_rules"] = get_area_occupancy_rules(ALL_AREAS)
        return area

    edited_area.id = area_id
    config_dict = extract_config()
    area_names = [x for x in config_dict.keys() if x.startswith("Area_")]
    areas = [map_section_from_config(x, config_dict) for x in area_names]
    areas_ids = [area["id"] for area in areas]
    try:
        index = areas_ids.index(area_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")

    cameras = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict, []) for x in cameras]
    camera_ids = [camera["id"] for camera in cameras]
    if not all(x in camera_ids for x in edited_area.cameras.split(",")):
        non_existent_cameras = set(edited_area.cameras.split(",")) - set(camera_ids)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The cameras: {non_existent_cameras}"
                                                                          f"do not exist")

    occupancy_rules = edited_area.occupancy_rules
    del edited_area.occupancy_rules

    area_dict = map_to_config_file_format(edited_area)
    config_dict[f"Area_{index}"] = area_dict
    success = update_config(config_dict, reboot_processor)

    if occupancy_rules:
        set_occupancy_rules(edited_area.id, occupancy_rules)
    else:
        delete_area_occupancy_rules(area_id)

    if not success:
        return handle_response(area_dict, success)
    area = next((area for area in get_areas() if area["id"] == area_id), None)
    area["occupancy_rules"] = get_area_occupancy_rules(area["id"])
    return area


@areas_router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(area_id: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the area <area_id>
    """
    if area_id.upper() == ALL_AREAS:
        delete_area_occupancy_rules(ALL_AREAS)
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Area with ID: 'ALL' cannot be deleted. However, its occupancy rules were deleted."
        )
    config_dict = extract_config()
    areas_name = [x for x in config_dict.keys() if x.startswith("Area_")]
    areas = [map_section_from_config(x, config_dict) for x in areas_name]
    areas_ids = [area["id"] for area in areas]
    try:
        index = areas_ids.index(area_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")

    config_dict.pop(f"Area_{index}")
    config_dict = reestructure_areas(config_dict)

    success = update_config(config_dict, reboot_processor)

    delete_area_occupancy_rules(area_id)

    area_directory = os.path.join(os.getenv("AreaLogDirectory"), area_id)
    shutil.rmtree(area_directory)
    area_config_directory = os.path.join(os.getenv("AreaConfigDirectory"), area_id)
    shutil.rmtree(area_config_directory)

    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


def get_area_occupancy_rules(area_id: str):
    """
    Returns time-based occupancy rules for an area.
    """
    config = get_config()
    areas = config.get_areas()
    area = next((area for area in areas if area.id == area_id), None)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")
    area_config_path = area.get_config_path()

    if not os.path.exists(area_config_path):
        return []

    with open(area_config_path, "r") as area_file:
        rules_data = json.load(area_file)
    return OccupancyRuleListDTO.from_store_json(rules_data)


def set_occupancy_rules(area_id: str, rules):
    area_config_path = get_config().get_area_config_path(area_id)
    Path(os.path.dirname(area_config_path)).mkdir(parents=True, exist_ok=True)

    if os.path.exists(area_config_path):
        with open(area_config_path, "r") as area_file:
            data = json.load(area_file)
    else:
        data = {}

    with open(area_config_path, "w") as area_file:
        data["occupancy_rules"] = rules.to_store_json()["occupancy_rules"]
        json.dump(data, area_file)


def delete_area_occupancy_rules(area_id: str):
    area_config_path = get_config().get_area_config_path(area_id)

    if os.path.exists(area_config_path):
        with open(area_config_path, "r") as area_file:
            data = json.load(area_file)
    else:
        return handle_response(None, False)

    with open(area_config_path, "w") as area_file:
        if data.get("occupancy_rules") is not None:
            del data["occupancy_rules"]
        json.dump(data, area_file)
