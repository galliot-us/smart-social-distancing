import os
import re
import tempfile
import logging

from datetime import date, datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from starlette import status
from typing import List, Tuple
from zipfile import ZipFile, ZIP_DEFLATED

from api.models.export import ExportDTO, ExportDataType
from api.utils import extract_config, clean_up_file
from libs.metrics import FaceMaskUsageMetric, OccupancyMetric, SocialDistancingMetric, InOutMetric, DwellTimeMetric

logger = logging.getLogger(__name__)

export_router = APIRouter()

# Define the exports data types as constants
ALL_DATA = ExportDataType.all_data
RAW_DATA = ExportDataType.raw_data
SOCIAL_DISTANCING = ExportDataType.social_distancing
FACEMASK_USAGE = ExportDataType.facemask_usage
IN_OUT = ExportDataType.in_out
OCCUPANCY = ExportDataType.occupancy
DWELL_TIME = ExportDataType.dwell_time


def export_folder_into_zip(source_path, destination_path, zip_file, from_date, to_date):
    """
    Export into the <zip_file> all the csv files included in the <source_path>.
    If the parameters <from_date> and <to_date> are sent, only the files between these days
    are exported.
    """
    if not os.path.exists(source_path):
        return None
    for filename in os.listdir(source_path):
        if filename.endswith(".csv"):
            if from_date and to_date:
                # Date range was specified, only include files in that range
                date_matches = re.findall(r"([0-9]{4}\-[0-9]{2}\-[0-9]{2})", filename)
                if not date_matches:
                    continue
                file_date = datetime.strptime(date_matches[0], '%Y-%m-%d').date()
                if not from_date <= file_date <= to_date:
                    continue
            zip_file.write(os.path.join(source_path, filename), arcname=os.path.join(destination_path, filename))


def get_areas_to_export(export_info: ExportDTO) -> List[Tuple[str, str]]:
    """
    Returns the list of areas (area_id, area_name) requested in the <export_info>.
    """
    all_areas = extract_config("areas").values()
    selected_areas = []
    if export_info.all_areas:
        selected_areas = all_areas
    else:
        selected_areas = [a for a in all_areas if a["Id"] in export_info.areas]
        if len(selected_areas) != len(export_info.areas):
            # Some of the selected areas don't exist
            missing_areas = set(export_info.areas) - set([a["Id"]for a in selected_areas])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Areas with ids {missing_areas} don't exist."
            )
    if selected_areas:
        return [(area["Id"], area["Name"]) for area in selected_areas]
    return []


def get_cameras_to_export(export_info: ExportDTO, areas: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """
    Returns the list of cameras (camera_id, camera_list) requested in the <export_info> and the cameras
    included in the <areas>.
    """
    all_cameras = extract_config("cameras").values()
    selected_cameras = []
    if export_info.all_cameras:
        selected_cameras = all_cameras
    else:
        selected_cameras = [c for c in all_cameras if c["Id"] in export_info.cameras]
        if len(selected_cameras) != len(export_info.cameras):
            # Some of the selected cameras don't exist
            missing_cameras = set(export_info.cameras) - set([c["Id"]for c in selected_cameras])
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cameras with ids {missing_cameras} don't exist."
            )
        # Include areas' cameras
        areas_cameras = []
        areas_ids = [a[0] for a in areas]
        for area in [a for a in extract_config("areas").values() if a['Id'] in areas_ids]:
            areas_cameras.extend(area["Cameras"].split(","))
        selected_cameras.extend(
            [c for c in all_cameras if c["Id"] in areas_cameras and c["Id"] not in export_info.cameras]
        )
    if selected_cameras:
        return [(camera["Id"], camera["Name"]) for camera in selected_cameras]
    return []


def export_camera_data_into_file(export_info: ExportDTO, camera_id: str, camera_name: str, zip_file: str) -> None:
    """
    Includes into the <zip_file> all the information requested in the <export_info> for the camera <camera_id>.
    """
    if ALL_DATA in export_info.data_types or RAW_DATA in export_info.data_types:
        object_logs_path = os.path.join(os.getenv("SourceLogDirectory"), camera_id, "objects_log")
        export_folder_into_zip(
            object_logs_path,
            os.path.join("cameras", f"{camera_id}-{camera_name}", "raw_data"),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )
    if ALL_DATA in export_info.data_types or SOCIAL_DISTANCING in export_info.data_types:
        social_ditancing_reports_folder = f"reports/{SocialDistancingMetric.reports_folder}"
        social_ditancing_reports_path = os.path.join(
            os.getenv("SourceLogDirectory"), camera_id, social_ditancing_reports_folder)
        export_folder_into_zip(
            social_ditancing_reports_path,
            os.path.join("cameras", f"{camera_id}-{camera_name}", social_ditancing_reports_folder),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )
    if ALL_DATA in export_info.data_types or DWELL_TIME in export_info.data_types:
        dwell_time_reports_folder = f"reports/{DwellTimeMetric.reports_folder}"
        dwell_time_reports_path = os.path.join(
            os.getenv("SourceLogDirectory"), camera_id, dwell_time_reports_folder)
        export_folder_into_zip(
            dwell_time_reports_path,
            os.path.join("cameras", f"{camera_id}-{camera_name}", dwell_time_reports_folder),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )
    if ALL_DATA in export_info.data_types or FACEMASK_USAGE in export_info.data_types:
        face_mask_reports_folder = f"reports/{FaceMaskUsageMetric.reports_folder}"
        face_mask_reports_path = os.path.join(
            os.getenv("SourceLogDirectory"), camera_id, face_mask_reports_folder)
        export_folder_into_zip(
            face_mask_reports_path,
            os.path.join("cameras", f"{camera_id}-{camera_name}", face_mask_reports_folder),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )
    if ALL_DATA in export_info.data_types or IN_OUT in export_info.data_types:
        in_out_reports_folder = f"reports/{InOutMetric.reports_folder}"
        in_out_reports_path = os.path.join(
            os.getenv("SourceLogDirectory"), camera_id, in_out_reports_folder)
        export_folder_into_zip(
            in_out_reports_path,
            os.path.join("cameras", f"{camera_id}-{camera_name}", in_out_reports_folder),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )


def export_area_data_into_file(export_info: ExportDTO, area_id: str, area_name: str, zip_file: str) -> None:
    """
    Includes into the <zip_file> all the information requested in the <export_info> for the area <area_id>.
    """
    if ALL_DATA in export_info.data_types or RAW_DATA in export_info.data_types:
        occupancy_logs_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
        export_folder_into_zip(
            occupancy_logs_path,
            os.path.join("areas", f"{area_id}-{area_name}", "raw_data"),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )
    if ALL_DATA in export_info.data_types or OCCUPANCY in export_info.data_types:
        occupancy_report_folder = f"reports/{OccupancyMetric.reports_folder}"
        occupancy_report_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, occupancy_report_folder)
        export_folder_into_zip(
            occupancy_report_path,
            os.path.join("areas", f"{area_id}-{area_name}", occupancy_report_folder),
            zip_file,
            export_info.from_date,
            export_info.to_date
        )


@export_router.put("")
async def export(export_info: ExportDTO, background_tasks: BackgroundTasks):
    """
    Returns a zip file containing the CSV files for the requested data.

    The endpoint allows filtering by:
    - *Entity*: (areas or cameras).
    - *Dates*: (only include data for the specified date range).
    - *Data Type*: (the type of information that you want to export. The available values are raw_data, occupancy,
        social-distancing, facemask-usage, in-out and all_data)
    """
    areas = get_areas_to_export(export_info)
    cameras = get_cameras_to_export(export_info, areas)
    temp_dir = tempfile.mkdtemp()
    export_filename = f"export-{date.today()}.zip"
    zip_path = os.path.join(temp_dir, export_filename)
    with ZipFile(zip_path, 'w', compression=ZIP_DEFLATED) as export_zip:
        for (cam_id, name) in cameras:
            export_camera_data_into_file(export_info, cam_id, name, export_zip)
        for (area_id, name) in areas:
            export_area_data_into_file(export_info, area_id, name, export_zip)
    background_tasks.add_task(clean_up_file, temp_dir)
    return FileResponse(zip_path, filename=export_filename)
