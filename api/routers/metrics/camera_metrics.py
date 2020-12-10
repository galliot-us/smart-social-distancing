import os

from datetime import date, timedelta
from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from api.models.metrics import (
    FaceMaskDaily, FaceMaskLive, FaceMaskHourly, FaceMaskWeekly, HeatmapReport,
    SocialDistancingDaily, SocialDistancingHourly, SocialDistancingLive,
    SocialDistancingWeekly)
from api.utils import extract_config
from libs.metrics import FaceMaskUsageMetric, SocialDistancingMetric
from libs.metrics.utils import generate_heatmap

metrics_router = APIRouter()


def get_all_cameras() -> str:
    config = extract_config(config_type="cameras")
    return ",".join([x["Id"] for x in config.values()])


def validate_dates(from_date, to_date):
    if from_date > to_date:
        raise HTTPException(status_code=400, detail="Invalid range of dates")


def validate_camera_existence(camera_id: str):
    dir_path = os.path.join(os.getenv("SourceLogDirectory"), camera_id, "objects_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail=f"Camera with id '{camera_id}' does not exist")


@metrics_router.get("/{camera_id}/heatmap", response_model=HeatmapReport)
def get_heatmap(camera_id: str,
                from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
                to_date: date = Query(date.today().isoformat()),
                report_type: Optional[str] = "violations"):
    """
    Returns a heatmap image displaying the violations/detections detected by the camera <camera_id>
    """
    validate_camera_existence(camera_id)
    if report_type in ["violations", "detections"]:
        return generate_heatmap(camera_id, from_date, to_date, report_type)
    else:
        raise HTTPException(status_code=400, detail="Invalid report_type")

# Social Distancing Metrics
@metrics_router.get("/social-distancing/live", response_model=SocialDistancingLive)
def get_camera_distancing_live(cameras: str = ""):
    """
    Returns a report with live information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return SocialDistancingMetric.get_live_report(cameras.split(","))


@metrics_router.get("/social-distancing/hourly", response_model=SocialDistancingHourly)
def get_camera_distancing_hourly_report(cameras: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return SocialDistancingMetric.get_hourly_report(cameras.split(","), date)


@metrics_router.get("/social-distancing/daily", response_model=SocialDistancingDaily)
def get_camera_distancing_daily_report(cameras: str = "",
                                       from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                       to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    validate_dates(from_date, to_date)
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return SocialDistancingMetric.get_daily_report(cameras.split(","), from_date, to_date)


@metrics_router.get("/social-distancing/weekly", response_model=SocialDistancingWeekly)
def get_camera_distancing_weekly_report(
        cameras: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a weekly report (for the date range specified) with information about the social distancing
    infractions detected in the cameras <cameras>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return SocialDistancingMetric.get_weekly_report(cameras.split(","), number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return SocialDistancingMetric.get_weekly_report(cameras.split(","), from_date=from_date, to_date=to_date)


# Face Mask Metrics
@metrics_router.get("/face-mask-detections/live", response_model=FaceMaskLive)
def get_camera_face_mask_detections_live(cameras: str = ""):
    """
    Returns a report with live information about the facemasks detected in the
    cameras <cameras>.
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return FaceMaskUsageMetric.get_live_report(cameras.split(","))


@metrics_router.get("/face-mask-detections/hourly", response_model=FaceMaskHourly)
def get_camera_face_mask_detections_hourly_report(cameras: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return FaceMaskUsageMetric.get_hourly_report(cameras.split(","), date)


@metrics_router.get("/face-mask-detections/daily", response_model=FaceMaskDaily)
def get_camera_face_mask_detections_daily_report(cameras: str = "",
                                                 from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                                 to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    validate_dates(from_date, to_date)
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    return FaceMaskUsageMetric.get_daily_report(cameras.split(","), from_date, to_date)


@metrics_router.get("/face-mask-detections/weekly", response_model=FaceMaskWeekly)
def get_camera_face_mask_detections_weekly_report(
        cameras: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a weekly report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    if not cameras:
        cameras = get_all_cameras()
    for camera in cameras.split(","):
        validate_camera_existence(camera)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return FaceMaskUsageMetric.get_weekly_report(cameras.split(","), number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return FaceMaskUsageMetric.get_weekly_report(cameras.split(","), from_date=from_date, to_date=to_date)
