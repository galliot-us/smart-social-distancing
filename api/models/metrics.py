from typing import List

from .base import SnakeModel


class HeatmapReport(SnakeModel):
    heatmap: List[List[float]]
    not_found_dates: List[str]

    class Config:
        schema_extra = {
            "example": [{
                "heatmap": "[[0.0,3.0,1.0,2.0,...],[3.0,1.34234,5.2342342,...],...]",
                "not_found_dates": [
                    "2020-08-14",
                    "2020-08-15",
                    "2020-08-16"
                ]
            }]
        }


class HourlyReports(SnakeModel):
    Hours: List[int]


class DailyReport(SnakeModel):
    Dates: List[str]


class WeeklyReport(SnakeModel):
    Weeks: List[str]


class LiveReport(SnakeModel):
    Time: str
    Trend: float


class SocialDistancing(SnakeModel):
    DetectedObjects: List[int]
    NoInfringement: List[int]
    LowInfringement: List[int]
    HighInfringement: List[int]
    CriticalInfringement: List[int]


class SocialDistancingLive(LiveReport):
    DetectedObjects: int
    NoInfringement: int
    LowInfringement: int
    HighInfringement: int
    CriticalInfringement: int


class SocialDistancingHourly(HourlyReports, SocialDistancing):
    class Config:
        schema_extra = {
            "example": [{
                "hours": list(range(0, 23)),
                "detected_objects": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                     0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0],
                "no_infringement": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                    0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "low_infringement": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                     0, 7273, 10011, 0, 0., 7273, 10011, 0, 0, 7273, 10011, 0],
                "high_infringement": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                      0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "critical_infringement": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                          0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0]
            }]
        }


class SocialDistancingDaily(DailyReport, SocialDistancing):
    class Config:
        schema_extra = {
            "example": [{
                "dates": ["2020-08-15", "2020-08-16", "2020-08-17", "2020-08-18"],
                "detected_objects": [0, 7273, 10011, 0],
                "no_infringement": [0, 4920, 6701, 0],
                "low_infringement": [0, 7273, 10011, 0],
                "high_infringement": [0, 4920, 6701, 0],
                "critical_infringement": [0, 4920, 6701, 0],
            }]
        }


class SocialDistancingWeekly(WeeklyReport, SocialDistancing):
    class Config:
        schema_extra = {
            "example": [{
                "weeks": ["2020-07-03 2020-07-05", "2020-07-06 2020-07-12", "2020-07-13 2020-07-19", "2020-07-20 2020-07-26"],
                "detected_objects": [0, 7273, 10011, 0],
                "no_infringement": [0, 4920, 6701, 0],
                "low_infringement": [0, 7273, 10011, 0],
                "high_infringement": [0, 4920, 6701, 0],
                "critical_infringement": [0, 4920, 6701, 0],
            }]
        }


class FaceMask(SnakeModel):
    NoFace: List[int]
    FaceWithMask: List[int]
    FaceWithoutMask: List[int]


class FaceMaskLive(LiveReport):
    NoFace: int
    FaceWithMask: int
    FaceWithoutMask: int


class FaceMaskHourly(HourlyReports, FaceMask):
    class Config:
        schema_extra = {
            "example": [{
                "hours": list(range(0, 23)),
                "no_face": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                            0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0],
                "face_with_mask": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                   0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "face_without_mask": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                      0, 7273, 10011, 0, 0., 7273, 10011, 0, 0, 7273, 10011, 0],
            }]
        }


class FaceMaskDaily(DailyReport, FaceMask):
    class Config:
        schema_extra = {
            "example": [{
                "dates": ["2020-08-15", "2020-08-16", "2020-08-17", "2020-08-18"],
                "no_face": [0, 7273, 10011, 0],
                "face_without_mask": [0, 4920, 6701, 0],
                "face_with_mask": [0, 7273, 10011, 0],
            }]
        }


class FaceMaskWeekly(WeeklyReport, FaceMask):
    class Config:
        schema_extra = {
            "example": [{
                "weeks": ["2020-07-03 2020-07-05", "2020-07-06 2020-07-12", "2020-07-13 2020-07-19", "2020-07-20 2020-07-26"],
                "no_face": [0, 7273, 10011, 0],
                "face_without_mask": [0, 4920, 6701, 0],
                "face_with_mask": [0, 7273, 10011, 0],
            }]
        }


class Occupancy(SnakeModel):
    OccupancyThreshold: List[int]
    AverageOccupancy: List[float]
    MaxOccupancy: List[float]


class OccupancyLive(LiveReport):
    AverageOccupancy: int
    MaxOccupancy: int
    OccupancyThreshold: int
    Violations: int


class OccupancyHourly(HourlyReports, Occupancy):
    class Config:
        schema_extra = {
            "example": [{
                "hours": list(range(0, 23)),
                "average_occupancy": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                      0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0],
                "max_occupancy": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                  0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0]
            }]
        }


class OccupancyDaily(DailyReport, Occupancy):
    class Config:
        schema_extra = {
            "example": [{
                "dates": ["2020-08-15", "2020-08-16", "2020-08-17", "2020-08-18"],
                "average_occupancy": [0, 7273, 10011, 0],
                "max_occupancy": [0, 4920, 6701, 0],
            }]
        }


class OccupancyWeekly(WeeklyReport, Occupancy):
    class Config:
        schema_extra = {
            "example": [{
                "weeks": ["2020-07-03 2020-07-05", "2020-07-06 2020-07-12", "2020-07-13 2020-07-19", "2020-07-20 2020-07-26"],
                "average_occupancy": [0, 7273, 10011, 0],
                "max_occupancy": [0, 4920, 6701, 0],
            }]
        }
