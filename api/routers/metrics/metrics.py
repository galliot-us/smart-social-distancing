import os

from datetime import date
from fastapi import HTTPException, status
from typing import Iterator

from api.utils import bad_request_serializer, extract_config
from constants import AREAS, CAMERAS, FACEMASK_USAGE, OCCUPANCY, SOCIAL_DISTANCING, IN_OUT, ALL_AREAS, DWELL_TIME
from libs.metrics import FaceMaskUsageMetric, OccupancyMetric, SocialDistancingMetric, InOutMetric, DwellTimeMetric


CAMERAS_METRICS = [SOCIAL_DISTANCING, FACEMASK_USAGE, IN_OUT]


def get_cameras(cameras: str) -> Iterator[str]:
    if cameras:
        return cameras.split(",")
    config = extract_config(config_type=CAMERAS)
    return [x["Id"] for x in config.values()]


def get_all_cameras() -> Iterator[str]:
    config = extract_config(config_type=CAMERAS)
    return [x["Id"] for x in config.values()]


def validate_camera_existence(camera_id: str):
    dir_path = os.path.join(os.getenv("SourceLogDirectory"), camera_id, "objects_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Camera with id '{camera_id}' does not exist")


def get_areas(areas: str) -> Iterator[str]:
    if ALL_AREAS in areas.upper().split(","):
        return [ALL_AREAS]
    if areas:
        return areas.split(",")
    config = extract_config(config_type=AREAS)
    return [x["Id"] for x in config.values()]


def get_cameras_for_areas(areas: Iterator[str]) -> Iterator[str]:
    if areas == [ALL_AREAS]:
        return get_all_cameras()
    config = extract_config(config_type=AREAS)
    cameras = []
    for area_config in config.values():
        if area_config["Id"] in areas:
            cameras.extend(area_config[CAMERAS.capitalize()].split(","))
    return cameras


def validate_area_existence(area_id: str):
    if area_id != ALL_AREAS:
        dir_path = os.path.join(os.getenv("AreaLogDirectory"), area_id, "occupancy_log")
        if not os.path.exists(dir_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Area with id '{area_id}' does not exist")


def validate_dates(from_date: date, to_date: date):
    if from_date > to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bad_request_serializer(
                "Invalid range of dates",
                error_type="from_date doesn't come before to_date",
                loc=["query", "from_date"]
            )
        )


def get_entities(entity: str, entities_ids: str, metric: str):
    entities = []
    if entity == CAMERAS:
        entities = get_cameras(entities_ids)
        for e in entities:
            validate_camera_existence(e)
    else:
        # entities == AREAS
        entities = get_areas(entities_ids)
        for e in entities:
            validate_area_existence(e)
    if entity == AREAS and metric in CAMERAS_METRICS:
        entities = get_cameras_for_areas(entities)
    if ALL_AREAS in entities_ids.upper() and entity == AREAS and metric == OCCUPANCY:
        # Occupancy is not a CAMERA_METRIC, it is an AREA_METRIC. So we have to return a list with all area ids.
        entities = get_areas("")
    return entities


def get_metric_class(metric: str):
    if metric == SOCIAL_DISTANCING:
        return SocialDistancingMetric
    elif metric == DWELL_TIME:
        return DwellTimeMetric
    elif metric == FACEMASK_USAGE:
        return FaceMaskUsageMetric
    elif metric == OCCUPANCY:
        return OccupancyMetric
    elif metric == IN_OUT:
        return InOutMetric
    else:
        raise ValueError(f"Metric {metric} not supported.")


def get_live_metric(entity: str, entities_ids: str, metric: str):
    entities = get_entities(entity, entities_ids, metric)
    metric_class = get_metric_class(metric)
    return metric_class.get_live_report(entities)


def get_hourly_metric(entity: str, entities_ids: str, metric: str, date: date):
    entities = get_entities(entity, entities_ids, metric)
    metric_class = get_metric_class(metric)
    return metric_class.get_hourly_report(entities, date)


def get_daily_metric(entity: str, entities_ids: str, metric: str, from_date: date,
                     to_date: date):
    validate_dates(from_date, to_date)
    entities = get_entities(entity, entities_ids, metric)
    metric_class = get_metric_class(metric)
    return metric_class.get_daily_report(entities, from_date, to_date)


def get_weekly_metric(entity: str, entities_ids: str, metric: str, from_date: date,
                      to_date: date, weeks: int):
    entities = get_entities(entity, entities_ids, metric)
    metric_class = get_metric_class(metric)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return metric_class.get_weekly_report(entities, number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return metric_class.get_weekly_report(entities, from_date=from_date, to_date=to_date)
