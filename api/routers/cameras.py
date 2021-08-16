import base64
import cv2 as cv
import logging
import os
import shutil
import re
import json
import numpy as np

from fastapi import APIRouter, status
from starlette.exceptions import HTTPException
from typing import Dict, Optional
from pathlib import Path

from libs.utils.camera_calibration import (get_camera_calibration_path, compute_and_save_inv_homography_matrix,
                                           ConfigHomographyMatrix)

from api.settings import Settings
from api.utils import (
    extract_config, get_config, handle_response, reestructure_areas, restart_processor,
    update_config, map_section_from_config, map_to_config_file_format, bad_request_serializer
)
from api.models.camera import (CameraDTO, CamerasListDTO, CreateCameraDTO, ImageModel, VideoLiveFeedModel,
                               ContourRoI, InOutBoundaries)
from libs.source_post_processors.objects_filtering import ObjectsFilteringPostProcessor
from libs.metrics.in_out import InOutMetric
from libs.utils.utils import validate_file_exists_and_is_not_empty

logger = logging.getLogger(__name__)

cameras_router = APIRouter()

settings = Settings()


def map_camera(camera_name, config, options=[]):
    camera_dict = map_section_from_config(camera_name, config)
    camera = config.get(camera_name)
    camera_id = camera.get("Id")
    image_string = None
    if "withImage" in options:
        image_string = get_camera_default_image_string(camera_id)
    camera_dict["image"] = image_string
    calibration_file_path = get_camera_calibration_path(settings.config, camera_id)
    camera_dict["has_been_calibrated"] = validate_file_exists_and_is_not_empty(calibration_file_path)
    roi_file_path = ObjectsFilteringPostProcessor.get_roi_file_path(camera_id, settings.config)
    camera_dict["has_defined_roi"] = validate_file_exists_and_is_not_empty(roi_file_path)
    in_out_file_path = InOutMetric.get_in_out_file_path(camera_id, settings.config)
    camera_dict["has_in_out_border"] = validate_file_exists_and_is_not_empty(in_out_file_path)
    return camera_dict


def get_cameras(options=[]):
    config = extract_config(config_type="cameras")
    return [map_camera(x, config, options) for x in config.keys()]


def map_to_camera_file_format(camera: CameraDTO):
    camera_file = map_to_config_file_format(camera)
    camera_file.pop("Image", None)
    return camera_file


def get_current_image(camera_id):
    camera = next((camera for camera in get_cameras() if camera["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    camera_cap = cv.VideoCapture(camera["videoPath"])
    if not camera_cap.isOpened():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The camera: {camera_id} is not available.")
    _, cv_image = camera_cap.read()
    resolution = tuple([int(i) for i in os.environ.get("Resolution").split(",")])
    cv_image = cv.resize(cv_image, resolution)
    camera_cap.release()
    return cv_image


def get_camera_default_image_string(camera_id):
    dir_path = verify_path(os.environ .get("ScreenshotsDirectory"), camera_id)
    image_path = os.path.join(dir_path, "default.jpg")
    if not os.path.isfile(image_path) or os.path.getsize(image_path) == 0:
        # There is not default image, save the current frame as default
        cv_image = get_current_image(camera_id)
        cv.imwrite(image_path, cv_image)
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read())


def delete_camera_from_areas(camera_id, config_dict):
    areas = {key: config_dict[key] for key in config_dict.keys() if key.startswith("Area_")}
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


def get_camera_index(config_dict: Dict, camera_id: str) -> int:
    """
    Returns the section source index for the camera <camera_id>
    """
    camera_names = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict) for x in camera_names]
    cameras_ids = [camera["id"] for camera in cameras]
    try:
        index = cameras_ids.index(camera_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    return index


def retrieve_camera_from_id(camera_id: str, options=[]):
    camera = next((camera for camera in get_cameras(options) if camera["id"] == camera_id), None)
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"The camera: {camera_id} does not exist")
    return camera


def validate_camera_existence(camera_id: str):
    retrieve_camera_from_id(camera_id)


@cameras_router.get("", response_model=CamerasListDTO)
async def list_cameras(options: Optional[str] = ""):
    """
    Returns the list of cameras managed by the processor.
    """
    return {
        "cameras": get_cameras(options)
    }


@cameras_router.get("/{camera_id}", response_model=CameraDTO)
async def get_camera(camera_id: str):
    """
    Returns the configuration related to the camera <camera_id>
    """
    return retrieve_camera_from_id(camera_id)


def get_first_unused_id(cameras_ids):
    if not cameras_ids:
        return 0

    is_a_number = re.compile("^[0-9]+$")
    ids_numbers = [int(value) for value in cameras_ids if is_a_number.match(value)]

    if not ids_numbers:
        return 0

    ids_numbers.sort()
    for i in range(0, ids_numbers[len(ids_numbers)-1]+1):
        if ids_numbers[i] != i:
            return i
    return ids_numbers[-1] + 1


@cameras_router.post("", response_model=CameraDTO, status_code=status.HTTP_201_CREATED)
async def create_camera(new_camera: CreateCameraDTO, reboot_processor: Optional[bool] = True):
    """
    Adds a new camera to the processor.
    """
    config_dict = extract_config()
    cameras_name = [x for x in config_dict.keys() if x.startswith("Source_")]
    cameras = [map_camera(x, config_dict) for x in cameras_name]

    if new_camera.id is None:
        ids = [camera["id"] for camera in cameras]
        new_camera.id = str(get_first_unused_id(ids))
    elif new_camera.id in [camera["id"] for camera in cameras]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Camera already exists", error_type="config duplicated camera")
        )
    camera_dict = map_to_camera_file_format(new_camera)
    config_dict[f"Source_{len(cameras)}"] = camera_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(camera_dict, success, status.HTTP_201_CREATED)

    camera_screenshot_directory = os.path.join(os.environ.get("ScreenshotsDirectory"), new_camera.id)
    Path(camera_screenshot_directory).mkdir(parents=True, exist_ok=True)
    heatmap_directory = os.path.join(os.getenv("SourceLogDirectory"), new_camera.id, "objects_log")
    Path(heatmap_directory).mkdir(parents=True, exist_ok=True)
    source_config_directory = os.path.join(os.getenv("SourceConfigDirectory"), new_camera.id)
    Path(source_config_directory).mkdir(parents=True, exist_ok=True)

    return next((camera for camera in get_cameras() if camera["id"] == camera_dict["Id"]), None)


@cameras_router.put("/{camera_id}", response_model=CameraDTO)
async def edit_camera(camera_id: str, edited_camera: CreateCameraDTO, reboot_processor: Optional[bool] = True):
    """
    Edits the configuration related to the camera <camera_id>
    """
    edited_camera.id = camera_id
    config_dict = extract_config()
    index = get_camera_index(config_dict, camera_id)
    camera_dict = map_to_camera_file_format(edited_camera)
    config_dict[f"Source_{index}"] = map_to_camera_file_format(edited_camera)
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(camera_dict, success)
    return next((camera for camera in get_cameras(["withImage"]) if camera["id"] == camera_id), None)


@cameras_router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: str, reboot_processor: Optional[bool] = True):
    """
    Deletes the configuration related to the camera <camera_id>
    """
    config_dict = extract_config()
    index = get_camera_index(config_dict, camera_id)
    config_dict = delete_camera_from_areas(camera_id, config_dict)
    config_dict.pop(f"Source_{index}")
    config_dict = reestructure_cameras((config_dict))
    success = update_config(config_dict, reboot_processor)

    # Delete all directories related to a given camera.
    camera_screenshot_directory = os.path.join(os.environ.get("ScreenshotsDirectory"), camera_id)
    shutil.rmtree(camera_screenshot_directory)
    source_directory = os.path.join(os.getenv("SourceLogDirectory"), camera_id)
    shutil.rmtree(source_directory)
    source_config_directory = os.path.join(os.getenv("SourceConfigDirectory"), camera_id)
    shutil.rmtree(source_config_directory)

    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


@cameras_router.get("/{camera_id}/image", response_model=ImageModel)
async def get_camera_image(camera_id: str):
    """
    Gets the image related to the camera <camera_id>
    """
    validate_camera_existence(camera_id)
    return {
        "image": get_camera_default_image_string(camera_id)
    }


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
    validate_camera_existence(camera_id)
    cv_image = get_current_image(camera_id)
    _, buffer = cv.imencode(".jpg", cv_image)
    encoded_string = base64.b64encode(buffer)
    return {
        "image": encoded_string
    }


@cameras_router.get("/{camera_id}/video_live_feed_enabled", response_model=VideoLiveFeedModel)
async def get_video_live_feed_enabled(camera_id: str):
    """
    Returns *True* if the video live feed is enabled for the camera <camera_id>
    """
    config_dict = extract_config()
    index = get_camera_index(config_dict, camera_id)
    config = get_config()
    return {
        "enabled": config.get_boolean(f"Source_{index}", "LiveFeedEnabled")
    }


@cameras_router.put("/{camera_id}/enable_video_live_feed", status_code=status.HTTP_204_NO_CONTENT)
async def enable_video_live_feed(camera_id: str, disable_other_cameras: Optional[bool] = True):
    """
    Enables the video live feed for the camera <camera_id>.
    By default, the video live feed for the other cameras will be disabled. You can change that behavior sending the
    *disable_other_cameras* parameter in *False*.
    """
    config_dict = extract_config()
    index = get_camera_index(config_dict, camera_id)
    if disable_other_cameras:
        for camera_section in [x for x in config_dict.keys() if x.startswith("Source_")]:
            config_dict[camera_section]["LiveFeedEnabled"] = "False"
    config_dict[f"Source_{index}"]["LiveFeedEnabled"] = "True"
    success = update_config(config_dict, True)
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


@cameras_router.get("/{camera_id}/roi_contour")
async def get_roi_contour(camera_id: str):
    """
        Get the contour of the RoI
    """
    validate_camera_existence(camera_id)
    roi_file_path = ObjectsFilteringPostProcessor.get_roi_file_path(camera_id, settings.config)
    roi_contour = ObjectsFilteringPostProcessor.get_roi_contour(roi_file_path)
    if roi_contour is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There is no defined RoI for {camera_id}")
    return roi_contour.tolist()


@cameras_router.put("/{camera_id}/roi_contour", status_code=status.HTTP_201_CREATED)
async def add_or_replace_roi_contour(camera_id: str, body: ContourRoI, reboot_processor: Optional[bool] = True):
    """
        Define a RoI for a camera or replace its current one.
        A RoI is defined by a vector of [x,y] 2-tuples, that map to coordinates in the image.
    """
    validate_camera_existence(camera_id)
    roi_file_path = ObjectsFilteringPostProcessor.get_roi_file_path(camera_id, settings.config)
    dir_path = Path(roi_file_path).parents[0]
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    roi_contour = np.array(body.contour_roi, dtype=int)
    np.savetxt(roi_file_path, roi_contour, delimiter=',', fmt='%i')
    restart_processor() if reboot_processor else True
    return roi_contour.tolist()


@cameras_router.delete("/{camera_id}/roi_contour")
async def remove_roi_contour(camera_id: str, reboot_processor: Optional[bool] = True):
    """
        Delete the defined RoI for a camera.
    """
    validate_camera_existence(camera_id)
    roi_file_path = ObjectsFilteringPostProcessor.get_roi_file_path(camera_id, settings.config)
    if not validate_file_exists_and_is_not_empty(roi_file_path):
        detail = f"There is no defined RoI for {camera_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    os.remove(roi_file_path)
    success = restart_processor() if reboot_processor else True
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)


@cameras_router.get("/{camera_id}/in_out_boundaries")
async def get_in_out_boundaries(camera_id: str):
    """
        Get the In/Out Boundaries for a camera.
        Each In/Out boundary in the list is represented by a name and:
        Two coordinates `[x,y]` are given in 2-tuples `[A,B]`. These points form a **line**.
        - If someone crosses the **line** while having **A** to their right, they are going in the `in` direction (entering).
        - Crossing the **line** while having **A** to their left means they are going in the `out` direction (leaving).
    """
    validate_camera_existence(camera_id)
    in_out_file_path = InOutMetric.get_in_out_file_path(camera_id, settings.config)
    in_out_boundaries = InOutMetric.read_in_out_boundaries(in_out_file_path)
    if in_out_boundaries is None:
        error_detail = f"There is no defined In/Out Boundary for {camera_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_detail)
    return InOutBoundaries(**dict(in_out_boundaries))


@cameras_router.put("/{camera_id}/in_out_boundaries", status_code=status.HTTP_201_CREATED)
async def add_or_replace_in_out_boundaries(camera_id: str, body: InOutBoundaries, reboot_processor: Optional[bool] = True):
    """
        Create or replace the In/Out boundaries for a camera.
        Each In/Out boundary in the list is represented by a name and:
        Two coordinates `[x,y]` are given in 2-tuples `[A,B]`. These points form a **line**.
        - If someone crosses the **line** while having **A** to their right, they are going in the `in` direction (entering).
        - Crossing the **line** while having **A** to their left means they are going in the `out` direction (leaving).
    """
    validate_camera_existence(camera_id)
    in_out_file_path = InOutMetric.get_in_out_file_path(camera_id, settings.config)
    dir_path = Path(in_out_file_path).parents[0]
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    in_out_boundaries = body.dict()
    with open(in_out_file_path, "w") as outfile:
        json.dump(in_out_boundaries, outfile)
    restart_processor() if reboot_processor else True
    return body


@cameras_router.delete("/{camera_id}/in_out_boundaries")
async def remove_in_out_boundaries(camera_id: str, reboot_processor: Optional[bool] = True):
    """
        Delete the defined In/Out boundaries for a camera.
    """
    validate_camera_existence(camera_id)
    in_out_file_path = InOutMetric.get_in_out_file_path(camera_id, settings.config)
    if not validate_file_exists_and_is_not_empty(in_out_file_path):
        detail = f"There is no defined In/Out Boundary for {camera_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    os.remove(in_out_file_path)
    success = restart_processor() if reboot_processor else True
    return handle_response(None, success, status.HTTP_204_NO_CONTENT)
