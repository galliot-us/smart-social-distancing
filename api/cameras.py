import base64
import cv2 as cv
import logging
import numpy as np
import os

from fastapi import APIRouter, status
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from typing import List, Optional

from libs.utils.camera_calibration import (get_camera_calibration_path, compute_and_save_inv_homography_matrix,
                                           ConfigHomographyMatrix)

from .models.config_keys import SourceConfigDTO
from .settings import Settings
from .utils import (
    extract_config, get_config, handle_response, reestructure_areas,
    update_config
)

logger = logging.getLogger(__name__)

cameras_router = APIRouter()

settings = Settings()


class ImageModel(BaseModel):
    image: str

    class Config:
        schema_extra = {
            "example": {
                "image": "data:image/jpg;base64,iVBORw0KG..."
            }
        }


class CamerasListDTO(BaseModel):
    cameras: List[SourceConfigDTO]


def map_camera(camera_name, config, options=[]):
    camera = config.get(camera_name)
    camera_id = camera.get("Id")
    image = None
    if "withImage" in options:
        dir_path = os.path.join(get_config().get_section_dict("App")["ScreenshotsDirectory"], camera_id)
        image = base64.b64encode(cv.imread(f"{dir_path}/default.jpg"))

    return {
        "id": camera_id,
        "name": camera.get("Name"),
        "videoPath": camera.get("VideoPath"),
        "emails": camera.get("Emails"),
        "enableSlackNotifications": camera.get("EnableSlackNotifications"),
        "violationThreshold": camera.get("ViolationThreshold"),
        "notifyEveryMinutes": camera.get("NotifyEveryMinutes"),
        "dailyReport": camera.get("DailyReport"),
        "dailyReportTime": camera.get("DailyReportTime"),
        "image": image,
        "distMethod": camera.get("DistMethod")
    }


def get_cameras(options):
    config = extract_config(config_type="cameras")
    return [map_camera(x, config, options) for x in config.keys()]


def map_to_camera_file_format(camera: SourceConfigDTO):
    return dict(
        {
            "Name": camera.name,
            "VideoPath": camera.videoPath,
            "Id": camera.id,
            "Emails": camera.emails,
            "EnableSlackNotifications": str(camera.enableSlackNotifications),
            "Tags": camera.tags,
            "NotifyEveryMinutes": str(camera.notifyEveryMinutes),
            "ViolationThreshold": str(camera.violationThreshold),
            "DistMethod": camera.distMethod,
            "DailyReport": str(camera.dailyReport),
            "DailyReportTime": camera.dailyReportTime
        }
    )


def delete_camera_from_areas(camera_id, config_dict):
    areas = {key: config_dict[key] for key in config_dict.keys() if key.startswith("Area")}
    for key, area in areas.items():
        cameras = area["Cameras"].split(",")
        if camera_id in cameras:
            cameras.remove(camera_id)
            if len(cameras) == 0:
                logger.warning(f'After removing the camera "{camera_id}", the area "{area["Id"]} - {area["Name"]}" \
                               "was left with no cameras and deleted')
                config_dict.pop(key)
            else:
                config_dict[key]["Cameras"] = ",".join(cameras)

    config_dict = reestructure_areas(config_dict)
    return config_dict


def reestructure_cameras(config_dict):
    """Ensure that all [Source_0, Source_1, ...] are consecutive"""
    source_names = [x for x in config_dict.keys() if x.startswith("Source_")]
    source_names.sort()
    for index, source_name in enumerate(source_names):
        if f"Source_{index}" != source_name:
            config_dict[f"Source_{index}"] = config_dict[source_name]
            config_dict.pop(source_name)
    return config_dict


def verify_path(base, camera_id):
    dir_path = os.path.join(base, camera_id)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    return dir_path


@cameras_router.get("", response_model=CamerasListDTO)
async def list_cameras(options: Optional[str] = ""):
    """
    Returns the list of cameras managed by the processor.
    """
    return {
        "cameras": get_cameras(options)
    }


@cameras_router.get("/{camera_id}", response_model=SourceConfigDTO)
async def get_camera(camera_id: str):
    """
    Returns the configuration related to the camera <camera_id>
    """
    camera = next((camera for camera in get_cameras(["withImage"]) if camera["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    return camera


@cameras_router.post("", response_model=SourceConfigDTO, status_code=status.HTTP_201_CREATED)
async def create_camera(new_camera: SourceConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a new camera to the processor.
    """
    config_dict = extract_config()
    cameras_name = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict, []) for x in cameras_name]
    if new_camera.id in [camera["id"] for camera in cameras]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera already exists")
    camera_dict = map_to_camera_file_format(new_camera)
    config_dict[f"Source_{len(cameras)}"] = camera_dict
    success = update_config(config_dict, reboot_processor)
    return handle_response(camera_dict, success, status.HTTP_201_CREATED)


@cameras_router.put("/{camera_id}", response_model=SourceConfigDTO)
async def edit_camera(camera_id: str, edited_camera: SourceConfigDTO, reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the camera <camera_id>
    """
    edited_camera.id = camera_id
    config_dict = extract_config()
    camera_names = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict, []) for x in camera_names]
    cameras_ids = [camera["id"] for camera in cameras]
    try:
        index = cameras_ids.index(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")

    camera_dict = map_to_camera_file_format(edited_camera)
    config_dict[f"Source_{index}"] = map_to_camera_file_format(edited_camera)

    success = update_config(config_dict, reboot_processor)
    return handle_response(camera_dict, success)


@cameras_router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the camera <camera_id>
    """
    config_dict = extract_config()
    camera_names = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict) for x in camera_names]
    cameras_ids = [camera["id"] for camera in cameras]
    try:
        index = cameras_ids.index(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")

    config_dict = delete_camera_from_areas(camera_id, config_dict)

    config_dict.pop(f"Source_{index}")
    config_dict = reestructure_cameras((config_dict))
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


@cameras_router.get("/{camera_id}/image", response_model=ImageModel)
async def get_camera_image(camera_id: str):
    """
    Gets the image related to the camera <camera_id>
    """
    dir_path = verify_path(settings.config.get_section_dict("App")["ScreenshotsDirectory"], camera_id)
    with open(f"{dir_path}/default.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return {
        "image": encoded_string
    }


@cameras_router.put("/{camera_id}/image", status_code=status.HTTP_204_NO_CONTENT)
async def replace_camera_image(camera_id: str, body: ImageModel):
    """
    Replaces the image related to the camera <camera_id>
    """
    dir_path = verify_path(settings.config.get_section_dict("App")["ScreenshotsDirectory"], camera_id)
    try:
        decoded_image = base64.b64decode(body.image.split(",")[1])
        nparr = np.fromstring(decoded_image, np.uint8)
        cv_image = cv.imdecode(nparr, cv.IMREAD_COLOR)
        cv.imwrite(f"{dir_path}/default.jpg", cv_image)
    except Exception:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image format")


@cameras_router.post("/{camera_id}/homography_matrix", status_code=status.HTTP_204_NO_CONTENT)
async def config_calibrated_distance(camera_id: str, body: ConfigHomographyMatrix, reboot_processor: Optional[bool] = True):
    """
    Calibrates the camera <camera_id> receiving as input the coordinates of a square of size 3ft 3" by 3ft 3" (1m by 1m).
    """
    dir_source = next((source for source in settings.config.get_video_sources() if source["id"] == camera_id), None)
    if not dir_source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    dir_path = get_camera_calibration_path(settings.config, camera_id)
    compute_and_save_inv_homography_matrix(points=body, destination=dir_path)
    sections = settings.config.get_sections()
    config_dict = {}
    for section in sections:
        config_dict[section] = settings.config.get_section_dict(section)
    config_dict[dir_source["section"]]["DistMethod"] = "CalibratedDistance"
    success = update_config(config_dict, reboot_processor)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


@cameras_router.get("/{camera_id}/calibration_image", response_model=ImageModel)
async def get_camera_calibration_image(camera_id: str):
    """
    Gets the image required to calibrate the camera <camera_id>
    """
    logger.info("Camera id")
    logger.info(camera_id)
    camera = next((camera for camera in get_cameras(["withImage"]) if camera["id"] == camera_id), None)
    camera_cap = cv.VideoCapture(camera["videoPath"])
    if not camera_cap.isOpened():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The camera: {camera_id} is not available.")
    _, cv_image = camera_cap.read()
    resolution = tuple([int(i) for i in os.environ.get("Resolution").split(",")])
    cv_image = cv.resize(cv_image, resolution)
    _, buffer = cv.imencode(".jpg", cv_image)
    encoded_string = base64.b64encode(buffer)
    camera_cap.release()
    return {
        "image": encoded_string
    }
