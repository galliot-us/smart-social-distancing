import os

from datetime import date, timedelta
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from libs.utils.reports import ReportsService

reports_api = FastAPI()

reports = ReportsService()


class Report(BaseModel):
    detected_objects: List[int]
    violating_objects: List[int]
    detected_faces: List[int]
    faces_with_mask: List[int]


class HourlyReport(Report):
    hours: List[int]
    detected_objects: List[float]
    violating_objects: List[float]
    detected_faces: List[float]
    faces_with_mask: List[float]

    class Config:
        schema_extra = {
            'example': [{
                'hours': list(range(0, 23)),
                'detected_objects': [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                     0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0],
                'violating_objects': [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                      0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                'detected_faces': [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                   0, 7273, 10011, 0, 0., 7273, 10011, 0, 0, 7273, 10011, 0],
                'faces_with_mask': [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                    0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0]
            }]
        }


class DailyReport(Report):
    dates: List[str]

    class Config:
        schema_extra = {
            'example': [{
                'dates': ['Saturday 2020-08-15', 'Sunday 2020-08-16', 'Monday 2020-08-17', 'Tuesday 2020-08-18'],
                'detected_objects': [0, 7273, 10011, 0],
                'violating_objects': [0, 4920, 6701, 0],
                'detected_faces': [0, 7273, 10011, 0],
                'faces_with_mask': [0, 4920, 6701, 0],
            }]
        }


class WeeklyReport(Report):
    weeks: List[str]

    class Config:
        schema_extra = {
            'example': [{
                'weeks': ['2020-07-03 2020-07-05', '2020-07-06 2020-07-12', '2020-07-13 2020-07-19', '2020-07-20 2020-07-26'],
                'detected_objects': [0, 27500, 0, 8000],
                'violating_objects': [0, 15000, 0, 4000],
                'detected_faces': [0, 27500, 0, 8000],
                'faces_with_mask': [0, 15000, 0, 4000],
            }]
        }


class HeatmapReport(BaseModel):
    heatmap: List[List[float]]
    not_found_dates: List[str]

    class Config:
        schema_extra = {
            'example': [{
                "heatmap": "[[0.0,3.0,1.0,2.0,...],[3.0,1.34234,5.2342342,...],...]",
                "not_found_dates": [
                    "2020-08-14",
                    "2020-08-15",
                    "2020-08-16"
                ]
            }]
        }


def validate_dates(from_date, to_date):
    if from_date > to_date:
        raise HTTPException(status_code=400, detail='Invalid range of dates')


def validate_existence(camera_id):
    dir_path = os.path.join(os.getenv('LogDirectory'), camera_id, "objects_log")
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail=f'Camera with id "{camera_id}" does not exist')


@reports_api.get("/{camera_id}/hourly", response_model=HourlyReport)
def get_hourly_report(camera_id,
                      from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                      to_date: date = Query(date.today().isoformat())):
    validate_dates(from_date, to_date)
    validate_existence(camera_id)
    return reports.hourly_report(camera_id, from_date, to_date)


@reports_api.get("/{camera_id}/daily", response_model=DailyReport)
def get_daily_report(camera_id,
                     from_date: date = Query((date.today() - timedelta(days=3)).isoformat()),
                     to_date: date = Query(date.today().isoformat())):
    validate_dates(from_date, to_date)
    validate_existence(camera_id)
    return reports.daily_report(camera_id, from_date, to_date)


@reports_api.get("/{camera_id}/weekly", response_model=WeeklyReport)
def get_weekly_report(camera_id,
                      weeks: int = Query(0),
                      from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
                      to_date: date = Query(date.today().isoformat())):
    """
    **If `weeks` is provided and is a positive number:**
    - `from_date` and `to_date` are ignored.
    - Report spans from `weeks*7 + 1` days ago to yesterday.
    - Taking yesterday as the end of week.

    **Else:**
    - Report spans from `from_Date` to `to_date`.
    - Taking Sunday as the end of week
    """
    validate_existence(camera_id)
    if weeks > 0:
        # Report from weeks*7 days ago (grouped by week, ending on yesterday)
        return reports.weekly_report(camera_id, number_of_weeks=weeks)
    else:
        # Report from the defined date_range, weeks ending on Sunday.
        validate_dates(from_date, to_date)
        return reports.weekly_report(camera_id, from_date=from_date, to_date=to_date)


@reports_api.get("/{camera_id}/heatmap", response_model=HeatmapReport)
def get_heatmap(
    camera_id,
    from_date: date = Query((date.today() - timedelta(days=date.today().weekday(), weeks=4)).isoformat()),
    to_date: date = Query(date.today().isoformat()),
    report_type: Optional[str] = 'violations'
):
    validate_existence(camera_id)
    if report_type in ['violations', 'detections']:
        return reports.heatmap(camera_id, from_date, to_date, report_type)
    else:
        raise HTTPException(status_code=400, detail='Invalid report_type')


@reports_api.get("/{camera_id}/peak_hour_violations")
def get_peak_hour_violations(camera_id):
    validate_existence(camera_id)
    return {
        'peak_hour_violations': reports.peak_hour_violations(camera_id)
    }


@reports_api.get("/{camera_id}/average_violations")
def get_average_violations(camera_id):
    validate_existence(camera_id)
    return {
        'average_violations': reports.average_violations(camera_id)
    }


@reports_api.get('/camera_with_most_violations')
def get_camera_with_most_violations():
    return {
        'cam_id': reports.camera_with_most_violations()
    }
