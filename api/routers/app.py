import requests

from fastapi import APIRouter
from starlette import status
from starlette.exceptions import HTTPException
from typing import Optional

from api.models.app import AppDTO
from api.utils import (extract_config, handle_response, update_config,
                       map_section_from_config, map_to_config_file_format)

from .cameras import get_cameras

app_router = APIRouter()
dashboard_sync_router = APIRouter()

@app_router.get("", response_model=AppDTO)
def get_app_config():
    """
    Returns the app configuration of the processor
    """
    return map_section_from_config("App", extract_config())


@app_router.put("", response_model=AppDTO)
def update_app_config(app: AppDTO, reboot_processor: Optional[bool] = True):
    """
    Updates the app configuration of the processor
    """
    config_dict = extract_config()
    app_dict = map_to_config_file_format(app)
    config_dict["App"] = app_dict
    success = update_config(config_dict, reboot_processor)
    if not success:
        return handle_response(app_dict, success)
    return map_section_from_config("App", extract_config())


@dashboard_sync_router.put("/dashboard-sync", status_code=status.HTTP_200_OK)
def sync_dashboard():
    """
    Sync the processor data in the cloud dashbord
    """
    config_dict = extract_config()
    dashboard_url = config_dict["App"]["DashboardURL"]
    endpoint_url = f"{dashboard_url}api/processor/sync/cameras"
    authorization_token = config_dict["App"].get("DashboardAuthorizationToken")
    headers = {
        "content-type": "application/json",
        "Authorization": authorization_token
    }
    if not authorization_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization token"
        )
    cameras = [
        {
            "processor_camera_id": camera["id"],
            "name": camera["name"],
            "has_been_calibrated": camera["has_been_calibrated"]
        }
        for camera in get_cameras()
    ]
    response = requests.put(endpoint_url, json=cameras, headers=headers)
    if response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error syncing processor with dashbord"
        )
    return response.json()
