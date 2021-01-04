from datetime import date, timedelta
from fastapi import APIRouter, Query

from api.models.metrics import (
    FaceMaskDaily, FaceMaskHourly, FaceMaskWeekly, FaceMaskLive, SocialDistancingDaily, SocialDistancingHourly,
    SocialDistancingWeekly, SocialDistancingLive, OccupancyHourly, OccupancyDaily, OccupancyLive, OccupancyWeekly)
from .metrics import get_live_metric, get_hourly_metric, get_daily_metric, get_weekly_metric

metrics_router = APIRouter()


# Occupancy Metrics
@metrics_router.get("/occupancy/live", response_model=OccupancyLive)
def get_area_occupancy_live(areas: str = ""):
    """
    Returns a report with live information about the occupancy in the areas <areas>.
    """
    return get_live_metric("areas", areas, "occupancy")


@metrics_router.get("/occupancy/hourly", response_model=OccupancyHourly)
def get_area_occupancy_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the occupancy in
    the areas <areas>.
    """
    return get_hourly_metric("areas", areas, "occupancy", date)


@metrics_router.get("/occupancy/daily", response_model=OccupancyDaily)
def get_area_occupancy_daily_report(areas: str = "",
                                    from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                    to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the occupancy in
    the areas <areas>.
    """
    return get_daily_metric("areas", areas, "occupancy", from_date, to_date)


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
    return get_weekly_metric("areas", areas, "occupancy", from_date, to_date, weeks)


# Social Distancing Metrics
@metrics_router.get("/social-distancing/live", response_model=SocialDistancingLive)
def get_camera_face_mask_detections_live(areas: str = ""):
    """
    Returns a report with live information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_live_metric("areas", areas, "social-distancing")


@metrics_router.get("/social-distancing/hourly", response_model=SocialDistancingHourly)
def get_area_distancing_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_hourly_metric("areas", areas, "social-distancing", date)


@metrics_router.get("/social-distancing/daily", response_model=SocialDistancingDaily)
def get_area_distancing_daily_report(areas: str = "",
                                     from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                     to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_daily_metric("areas", areas, "social-distancing", from_date, to_date)


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
    return get_weekly_metric("areas", areas, "social-distancing", from_date, to_date, weeks)


# Face Mask Metrics
@metrics_router.get("/face-mask-detections/live", response_model=FaceMaskLive)
def get_area_face_mask_detections_live(areas: str = ""):
    """
    Returns a report with live information about the facemasks detected in the areas <areas>.
    """
    return get_live_metric("areas", areas, "facemask-usage")


@metrics_router.get("/face-mask-detections/hourly", response_model=FaceMaskHourly)
def get_area_face_mask_detections_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_hourly_metric("areas", areas, "facemask-usage", date)


@metrics_router.get("/face-mask-detections/daily", response_model=FaceMaskDaily)
def get_area_face_mask_detections_daily_report(areas: str = "",
                                               from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                               to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_daily_metric("areas", areas, "facemask-usage", from_date, to_date)


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
    return get_weekly_metric("areas", areas, "facemask-usage", from_date, to_date, weeks)
