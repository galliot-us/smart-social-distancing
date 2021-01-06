import os
import tempfile

from datetime import date
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from zipfile import ZipFile, ZIP_DEFLATED
from api.utils import extract_config, clean_up_file
from libs.metrics import FaceMaskUsageMetric, OccupancyMetric, SocialDistancingMetric

export_router = APIRouter()


def validate_camera_existence(camera_id: str):
    dir_path = os.path.join(os.getenv("SourceLogDirectory"), camera_id, "objects_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with id '{camera_id}' does not exist")


def validate_area_existence(area_id: str):
    dir_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Area with id '{area_id}' does not exist")


@export_router.get("/camera/{camera_id}/daily_data")
def get_camera_daily_data(camera_id: str, date: date = Query(date.today().isoformat())):
    """
    Returns a csv file containing the data detected by the camera <camera_id> for the date <date>
    """
    validate_camera_existence(camera_id)
    dir_path = os.path.join(os.getenv("SourceLogDirectory"), camera_id, "objects_log")
    if not os.path.exists(os.path.join(dir_path, f"{date}.csv")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There is no data for the selected date.")
    return FileResponse(f"{dir_path}/{date}.csv", media_type="text/csv", filename=f"{date}_daily_data.csv")


@export_router.get("/area/{area_id}/daily_data")
def get_area_daily_data(area_id: str, date: date = Query(date.today().isoformat())):
    """
    Returns a csv file containing the data detected by the area <area_id> for the date <date>
    """
    validate_area_existence(area_id)
    dir_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
    if not os.path.exists(os.path.join(dir_path, f"{date}.csv")):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"There is no data for the selected date.")
    return FileResponse(f"{dir_path}/{date}.csv", media_type="text/csv", filename=f"{date}_daily_data.csv")


def export_folder_into_zip(source_path, destination_path, zip_file):
    if not os.path.exists(source_path):
        return None
    for filename in os.listdir(source_path):
        if filename.endswith(".csv"):
            zip_file.write(os.path.join(source_path, filename), arcname=os.path.join(destination_path, filename))


@export_router.get("/export_all")
async def export_all_data(background_tasks: BackgroundTasks):
    """
    Returns a zip file containing the csv files for all cameras and areas
    """
    # TODO: Improve this function
    cameras = [(section_dict["Id"], section_dict["Name"]) for section_dict in extract_config("cameras").values()]
    areas = [(section_dict["Id"], section_dict["Name"]) for section_dict in extract_config("areas").values()]

    temp_dir = tempfile.mkdtemp()
    export_filename = f"export-{date.today()}.zip"
    zip_path = os.path.join(temp_dir, export_filename)
    with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED) as export_zip:
        for (cam_id, name) in cameras:
            object_logs_path = os.path.join(os.getenv("SourceLogDirectory"), cam_id, "objects_log")
            social_ditancing_reports_folder = f"reports/{SocialDistancingMetric.reports_folder}"
            social_ditancing_reports_path = os.path.join(os.getenv("SourceLogDirectory"), cam_id,
                                                         social_ditancing_reports_folder)
            face_mask_reports_folder = f"reports/{FaceMaskUsageMetric.reports_folder}"
            face_mask_reports_path = os.path.join(os.getenv("SourceLogDirectory"), cam_id,
                                                  face_mask_reports_folder)
            export_folder_into_zip(object_logs_path, os.path.join(
                "cameras", f"{cam_id}-{name}", "raw_data"), export_zip)
            export_folder_into_zip(social_ditancing_reports_path, os.path.join(
                "cameras", f"{cam_id}-{name}", social_ditancing_reports_folder), export_zip)
            export_folder_into_zip(face_mask_reports_path, os.path.join(
                "cameras", f"{cam_id}-{name}", face_mask_reports_folder), export_zip)
        for (area_id, name) in areas:
            occupancy_logs_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
            occupancy_report_folder = f"reports/{OccupancyMetric.reports_folder}"
            occupancy_report_path = os.path.join(os.getenv("AreaLogDirectory"), area_id,
                                                 occupancy_report_folder)
            export_folder_into_zip(occupancy_logs_path, os.path.join(
                "areas", f"{area_id}-{name}", "raw_data"), export_zip)
            export_folder_into_zip(occupancy_report_path, os.path.join(
                "areas", f"{area_id}-{name}", occupancy_report_folder), export_zip)
    background_tasks.add_task(clean_up_file, temp_dir)
    return FileResponse(zip_path, filename=export_filename)
