from datetime import date, timedelta
from fastapi import APIRouter, Query

from api.models.metrics import (
    FaceMaskDaily, FaceMaskHourly, FaceMaskWeekly, FaceMaskLive, SocialDistancingDaily, SocialDistancingHourly,
    SocialDistancingWeekly, SocialDistancingLive, OccupancyHourly, OccupancyDaily, OccupancyLive, OccupancyWeekly,
    InOutLive, InOutHourly, InOutDaily, InOutWeekly,
    DwellTimeDaily, DwellTimeHourly, DwellTimeLive, DwellTimeWeekly)
from constants import AREAS, FACEMASK_USAGE, OCCUPANCY, SOCIAL_DISTANCING, IN_OUT, DWELL_TIME

from .metrics import get_live_metric, get_hourly_metric, get_daily_metric, get_weekly_metric

metrics_router = APIRouter()


# Occupancy MetricsAREAS
@metrics_router.get("/occupancy/live", response_model=OccupancyLive)
def get_area_occupancy_live(areas: str = ""):
    """
    Returns a report with live information about the occupancy in the areas <areas>.
    """
    return get_live_metric(AREAS, areas, OCCUPANCY)


@metrics_router.get("/occupancy/hourly", response_model=OccupancyHourly)
def get_area_occupancy_hourly_report(areas: str = "", date: date = Query(date.today())):
    """
    Returns a hourly report (for the date specified) with information about the occupancy in
    the areas <areas>.
    """
    return get_hourly_metric(AREAS, areas, OCCUPANCY, date)


@metrics_router.get("/occupancy/daily", response_model=OccupancyDaily)
def get_area_occupancy_daily_report(areas: str = "",
                                    from_date: date = Query((date.today() - timedelta(days=3))),
                                    to_date: date = Query(date.today())):
    """
    Returns a daily report (for the date range specified) with information about the occupancy in
    the areas <areas>.
    """
    return get_daily_metric(AREAS, areas, OCCUPANCY, from_date, to_date)


@metrics_router.get("/occupancy/weekly", response_model=OccupancyWeekly)
def get_area_occupancy_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4))),
        to_date: date = Query(date.today())):
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
    return get_weekly_metric(AREAS, areas, OCCUPANCY, from_date, to_date, weeks)


# Social Distancing Metrics
@metrics_router.get("/social-distancing/live", response_model=SocialDistancingLive)
def get_area_social_distancing_live(areas: str = ""):
    """
    Returns a report with live information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_live_metric(AREAS, areas, SOCIAL_DISTANCING)


@metrics_router.get("/social-distancing/hourly", response_model=SocialDistancingHourly)
def get_area_distancing_hourly_report(areas: str = "", date: date = Query(date.today())):
    """
    Returns a hourly report (for the date specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_hourly_metric(AREAS, areas, SOCIAL_DISTANCING, date)


@metrics_router.get("/social-distancing/daily", response_model=SocialDistancingDaily)
def get_area_distancing_daily_report(areas: str = "",
                                     from_date: date = Query((date.today() - timedelta(days=3))),
                                     to_date: date = Query(date.today())):
    """
    Returns a daily report (for the date range specified) with information about the social distancing infractions
    detected in the areas <areas>.
    """
    return get_daily_metric(AREAS, areas, SOCIAL_DISTANCING, from_date, to_date)


@metrics_router.get("/social-distancing/weekly", response_model=SocialDistancingWeekly)
def get_area_distancing_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4))),
        to_date: date = Query(date.today())):
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
    return get_weekly_metric(AREAS, areas, SOCIAL_DISTANCING, from_date, to_date, weeks)


# Dwell time Metrics
@metrics_router.get("/dwell-time/live", response_model=DwellTimeLive)
def get_area_dwell_time_live(areas: str = ""):
    """
    Returns a report with live information about the dwell time of people
    detected in the areas <areas>.
    """
    return get_live_metric(AREAS, areas, DWELL_TIME)


@metrics_router.get("/dwell-time/hourly", response_model=DwellTimeHourly)
def get_area_dwell_time_hourly_report(areas: str = "", date: date = Query(date.today())):
    """
    Returns a hourly report (for the date specified) with information about the duel time (⚔) of people
    detected in the areas <areas>.
    """
    return get_hourly_metric(AREAS, areas, DWELL_TIME, date)


@metrics_router.get("/dwell-time/daily", response_model=DwellTimeDaily)
def get_area_dwell_time_daily_report(areas: str = "",
                                     from_date: date = Query((date.today() - timedelta(days=3))),
                                     to_date: date = Query(date.today())):
    """
    Returns a daily report (for the date range specified) with information about the dwell time of people
    detected in the areas <areas>.
    """
    return get_daily_metric(AREAS, areas, DWELL_TIME, from_date, to_date)


@metrics_router.get("/dwell-time/weekly", response_model=DwellTimeWeekly)
def get_area_dwell_time_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4))),
        to_date: date = Query(date.today())):
    """
    Returns a weekly report (for the date range specified) with information about the ???
    detected in the areas <areas>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    return get_weekly_metric(AREAS, areas, DWELL_TIME, from_date, to_date, weeks)


# Face Mask Metrics
@metrics_router.get("/face-mask-detections/live", response_model=FaceMaskLive)
def get_area_face_mask_detections_live(areas: str = ""):
    """
    Returns a report with live information about the facemasks detected in the areas <areas>.
    """
    return get_live_metric(AREAS, areas, FACEMASK_USAGE)


@metrics_router.get("/face-mask-detections/hourly", response_model=FaceMaskHourly)
def get_area_face_mask_detections_hourly_report(areas: str = "", date: date = Query(date.today())):
    """
    Returns a hourly report (for the date specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_hourly_metric(AREAS, areas, FACEMASK_USAGE, date)


@metrics_router.get("/face-mask-detections/daily", response_model=FaceMaskDaily)
def get_area_face_mask_detections_daily_report(areas: str = "",
                                               from_date: date = Query((date.today() - timedelta(days=3))),
                                               to_date: date = Query(date.today())):
    """
    Returns a daily report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_daily_metric(AREAS, areas, FACEMASK_USAGE, from_date, to_date)


@metrics_router.get("/face-mask-detections/weekly", response_model=FaceMaskWeekly)
def get_area_face_mask_detections_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4))),
        to_date: date = Query(date.today())):
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
    return get_weekly_metric(AREAS, areas, FACEMASK_USAGE, from_date, to_date, weeks)


# In Out Metrics
@metrics_router.get("/in-out/live", response_model=InOutLive)
def get_camera_in_out_live(areas: str = ""):
    """
    Returns a report with live information about the in-out flow detected in the
    cameras <cameras>.
    """
    return get_live_metric(AREAS, areas, IN_OUT)


@metrics_router.get("/in-out/hourly", response_model=InOutHourly)
def get_camera_in_out_hourly_report(areas: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the in-out flow detected in
    the cameras <cameras>.
    """
    return get_hourly_metric(AREAS, areas, IN_OUT, date)


@metrics_router.get("/in-out/daily", response_model=InOutDaily)
def get_camera_in_out_daily_report(
        areas: str = "",
        from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the in-out flow detected in
    the cameras <cameras>.
    """
    return get_daily_metric(AREAS, areas, IN_OUT, from_date, to_date)


@metrics_router.get("/in-out/weekly", response_model=InOutWeekly)
def get_camera_in_out_weekly_report(
        areas: str = "",
        weeks: int = Query(0),
        from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
        to_date: date = Query(date.today().isoformat())):
    """
    Returns a weekly report (for the date range specified) with information about the in-out flow detected in
    the cameras <cameras>.

    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    return get_weekly_metric(AREAS, areas, IN_OUT, from_date, to_date, weeks)
