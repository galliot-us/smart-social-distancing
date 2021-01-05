from datetime import date, timedelta
from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional

from api.models.metrics import (
    FaceMaskDaily, FaceMaskLive, FaceMaskHourly, FaceMaskWeekly, HeatmapReport,
    SocialDistancingDaily, SocialDistancingHourly, SocialDistancingLive,
    SocialDistancingWeekly)
from api.utils import bad_request_serializer
from constants import CAMERAS, FACEMASK_USAGE, SOCIAL_DISTANCING
from libs.metrics.utils import generate_heatmap

from .metrics import (validate_camera_existence, get_live_metric, get_hourly_metric, get_daily_metric,
                      get_weekly_metric)

metrics_router = APIRouter()


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer("Invalid report_type", error_type="invalid config")
        )

# Social Distancing Metrics
@metrics_router.get("/social-distancing/live", response_model=SocialDistancingLive)
def get_camera_distancing_live(cameras: str = ""):
    """
    Returns a report with live information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    return get_live_metric(CAMERAS, cameras, SOCIAL_DISTANCING)


@metrics_router.get("/social-distancing/hourly", response_model=SocialDistancingHourly)
def get_camera_distancing_hourly_report(cameras: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    return get_hourly_metric(CAMERAS, cameras, SOCIAL_DISTANCING, date)


@metrics_router.get("/social-distancing/daily", response_model=SocialDistancingDaily)
def get_camera_distancing_daily_report(cameras: str = "",
                                       from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                       to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the social distancing infractions
    detected in the cameras <cameras>.
    """
    return get_daily_metric(CAMERAS, cameras, SOCIAL_DISTANCING, from_date, to_date)


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
    return get_weekly_metric(CAMERAS, cameras, SOCIAL_DISTANCING, from_date, to_date, weeks)


# Face Mask Metrics
@metrics_router.get("/face-mask-detections/live", response_model=FaceMaskLive)
def get_camera_face_mask_detections_live(cameras: str = ""):
    """
    Returns a report with live information about the facemasks detected in the
    cameras <cameras>.
    """
    return get_live_metric(CAMERAS, cameras, FACEMASK_USAGE)


@metrics_router.get("/face-mask-detections/hourly", response_model=FaceMaskHourly)
def get_camera_face_mask_detections_hourly_report(cameras: str = "", date: date = Query(date.today().isoformat())):
    """
    Returns a hourly report (for the date specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_hourly_metric(CAMERAS, cameras, FACEMASK_USAGE, date)


@metrics_router.get("/face-mask-detections/daily", response_model=FaceMaskDaily)
def get_camera_face_mask_detections_daily_report(cameras: str = "",
                                                 from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                                                 to_date: date = Query(date.today().isoformat())):
    """
    Returns a daily report (for the date range specified) with information about the facemasks detected in
    the cameras <cameras>.
    """
    return get_daily_metric(CAMERAS, cameras, FACEMASK_USAGE, from_date, to_date)


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
    return get_weekly_metric(CAMERAS, cameras, FACEMASK_USAGE, from_date, to_date, weeks)
