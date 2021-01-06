import os

from datetime import date, timedelta
from fastapi import APIRouter, Query, HTTPException, status
from typing import Iterator

from api.models.metrics import (
    FaceMaskDaily, FaceMaskHourly, FaceMaskWeekly, FaceMaskLive, SocialDistancingDaily, SocialDistancingHourly,
    SocialDistancingWeekly, SocialDistancingLive, OccupancyHourly, OccupancyDaily, OccupancyLive, OccupancyWeekly)
from api.utils import extract_config
from libs.metrics import FaceMaskUsageMetric, OccupancyMetric, SocialDistancingMetric

metrics_router = APIRouter()


def get_areas(areas: str) -> Iterator[str]:
    if areas:
        return areas.split(",")
    config = extract_config(config_type="areas")
    return [x["Id"] for x in config.values()]


def get_cameras_for_areas(areas: Iterator[str]) -> Iterator[str]:
    config = extract_config(config_type="areas")
    cameras = []
    for area_config in config.values():
        if area_config["Id"] in areas:
            cameras.extend(area_config["Cameras"].split(","))
    return cameras


def validate_dates(from_date: date, to_date: date):
    if from_date > to_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid range of dates")


def validate_area_existence(area_id: str):
    dir_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Area with id '{area_id}' does not exist")


# Occupancy Metrics
@metrics_router.get("/occupancy/live", response_model=OccupancyLive)
def get_area_occupancy_live(areas: str = ""):
    """
    Returns a report with live information about the occupancy in the areas <areas>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    return OccupancyMetric.get_live_report(areas)


@metrics_router.get("/occupancy/hourly", response_model=OccupancyHourly)
def get_area_occupancy_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the occupancy in
    the areas <areas>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    return OccupancyMetric.get_hourly_report(areas, date)


@metrics_router.get("/occupancy/daily", response_model=OccupancyDaily)
def get_area_occupancy_daily_report(areas: str = "",
                                    from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                    to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the occupancy in
    the areas <areas>.
    """
    validate_dates(from_date, to_date)
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    return OccupancyMetric.get_daily_report(areas, from_date, to_date)


@metrics_router.get("/occupancy/weekly", response_model=OccupancyWeekly)
def get_area_occupancy_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a weekly report (for the date range specified) with information about the occupancy in
    the areas <areas>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return OccupancyMetric.get_weekly_report(areas, number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return OccupancyMetric.get_weekly_report(areas, from_date=from_date, to_date=to_date)


# Social Distancing Metrics
@metrics_router.get("/social-distancing/live", response_model=SocialDistancingLive)
def get_camera_face_mask_detections_live(areas: str = ""):
    """
    Returns a report with live information about the social distancing infractions
    detected in the areas <areas>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return SocialDistancingMetric.get_live_report(cameras)


@metrics_router.get("/social-distancing/hourly", response_model=SocialDistancingHourly)
def get_area_distancing_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return SocialDistancingMetric.get_hourly_report(cameras, date)


@metrics_router.get("/social-distancing/daily", response_model=SocialDistancingDaily)
def get_area_distancing_daily_report(areas: str = "",
                                     from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                     to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    validate_dates(from_date, to_date)
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return SocialDistancingMetric.get_daily_report(cameras, from_date, to_date)


@metrics_router.get("/social-distancing/weekly", response_model=SocialDistancingWeekly)
def get_area_distancing_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a weekly report (for the date range specified) with information about the social distancing
    infractions detected in the areas <areas>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return SocialDistancingMetric.get_weekly_report(cameras, number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return SocialDistancingMetric.get_weekly_report(cameras, from_date=from_date, to_date=to_date)


# Face Mask Metrics
@metrics_router.get("/face-mask-detections/live", response_model=FaceMaskLive)
def get_area_face_mask_detections_live(areas: str = ""):
    """
    Returns a report with live information about the facemasks detected in the areas <areas>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return FaceMaskUsageMetric.get_live_report(cameras)


@metrics_router.get("/face-mask-detections/hourly", response_model=FaceMaskHourly)
def get_area_face_mask_detections_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return FaceMaskUsageMetric.get_hourly_report(cameras, date)


@metrics_router.get("/face-mask-detections/daily", response_model=FaceMaskDaily)
def get_area_face_mask_detections_daily_report(areas: str = "",
                                               from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                               to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    validate_dates(from_date, to_date)
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    return FaceMaskUsageMetric.get_daily_report(cameras, from_date, to_date)


@metrics_router.get("/face-mask-detections/weekly", response_model=FaceMaskWeekly)
def get_area_face_mask_detections_weekly_report(
        areas: str = "",
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
    areas = get_areas(areas)
    for area in areas:
        validate_area_existence(area)
    cameras = get_cameras_for_areas(areas)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return FaceMaskUsageMetric.get_weekly_report(cameras, number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return FaceMaskUsageMetric.get_weekly_report(cameras, from_date=from_date, to_date=to_date)
