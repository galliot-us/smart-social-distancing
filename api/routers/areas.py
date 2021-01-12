from fastapi import APIRouter, status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.area import AreaConfigDTO, AreasListDTO
from .cameras import map_camera
from api.utils import (
    extract_config, handle_response, reestructure_areas, update_config, map_section_from_config,
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


@areas_router.get("/{area_id}", response_model=AreaConfigDTO)
async def get_area(area_id: str):
    """
    Returns the configuration related to the area <area_id>
    """
    area = next((area for area in get_areas() if area["id"] == area_id), None)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")
    return area


@areas_router.post("", response_model=AreaConfigDTO, status_code=status.HTTP_201_CREATED)
async def create_area(new_area: AreaConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a new area to the processor.
    """
    config_dict = extract_config()
    areas_name = [x for x in config_dict.keys() if x.startswith("Area_")]
    areas = [map_section_from_config(x, config_dict) for x in areas_name]
    if new_area.id in [area["id"] for area in areas]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Area already exists", error_type="config duplicated area")
        )

    cameras = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict, []) for x in cameras]
    camera_ids = [camera["id"] for camera in cameras]
    if not all(x in camera_ids for x in new_area.cameras.split(",")):
        non_existent_cameras = set(new_area.cameras.split(",")) - set(camera_ids)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The cameras: {non_existent_cameras} do not exist")
    area_dict = map_to_config_file_format(new_area)
    config_dict[f"Area_{len(areas)}"] = area_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(area_dict, success, status.HTTP_201_CREATED)
    return next((area for area in get_areas() if area["id"] == area_dict["Id"]), None)


@areas_router.put("/{area_id}", response_model=AreaConfigDTO)
async def edit_area(area_id: str, edited_area: AreaConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the area <area_id>
    """
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The cameras: {non_existent_cameras} do not exist")

    area_dict = map_to_config_file_format(edited_area)
    config_dict[f"Area_{index}"] = area_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(area_dict, success)
    return next((area for area in get_areas() if area["id"] == area_id), None)


@areas_router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(area_id: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the area <area_id>
    """
    config_dict = extract_config()
    areas_name = [x for x in config_dict.keys() if x.startswith("Area_")]
    areas = [map_section_from_config(x, config_dict) for x in areas_name]
    areas_ids = [area["id"] for area in areas]
    try:
        index = areas_ids.index(area_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The area: {area_id} does not exist")

    config_dict.pop(f"Area_{index}")
    config_dict = reestructure_areas((config_dict))

    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
