from typing import List, Tuple

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


class DwellTime(SnakeModel):
    DetectedObjects: List[int]
    AvgDwellTime: List[float]
    MaxDwellTime: List[int]
    L1: List[int]
    L2: List[int]
    L3: List[int]
    L4: List[int]
    L5: List[int]


class DwellTimeLive(LiveReport):
    DetectedObjects: int
    AvgDwellTime: float
    MaxDwellTime: int
    L1: int
    L2: int
    L3: int
    L4: int
    L5: int


class DwellTimeHourly(HourlyReports, DwellTime):
    class Config:
        schema_extra = {
            "example": [{
                "hours": list(range(0, 23)),
                "detected_objects": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                                     0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0],
                "l1": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                       0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "l2": [0, 7273, 10011, 0, 0, 7273, 10011, 0, 0, 7273, 10011, 0,
                       0, 7273, 10011, 0, 0., 7273, 10011, 0, 0, 7273, 10011, 0],
                "l3": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                       0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "l4": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                       0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "l5": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                       0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
                "avg_dwell_time": [0.0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0.0,
                                   0.0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0.0],
                "max_dwell_time": [0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0,
                                   0, 4920, 6701, 0, 0, 4920, 6701, 0, 0, 4920, 6701, 0],
            }]
        }


class DwellTimeDaily(DailyReport, DwellTime):
    class Config:
        schema_extra = {
            "example": [{
                "dates": ["2020-08-15", "2020-08-16", "2020-08-17", "2020-08-18"],
                "detected_objects": [0, 7273, 10011, 0],
                "l1": [0, 4920, 6701, 0],
                "l2": [0, 7273, 10011, 0],
                "l3": [0, 4920, 6701, 0],
                "l4": [0, 4920, 6701, 0],
                "l5": [0, 4920, 6701, 0],
                "avg_dwell_time": [0.0, 4920, 6701, 0],
                "max_dwell_time": [0, 4920, 6701, 0],
            }]
        }


class DwellTimeWeekly(WeeklyReport, DwellTime):
    class Config:
        schema_extra = {
            "example": [{
                "weeks": ["2020-07-03 2020-07-05", "2020-07-06 2020-07-12", "2020-07-13 2020-07-19", "2020-07-20 2020-07-26"],
                "l1": [0, 4920, 6701, 0],
                "l2": [0, 7273, 10011, 0],
                "l3": [0, 4920, 6701, 0],
                "l4": [0, 4920, 6701, 0],
                "l5": [0, 4920, 6701, 0],
                "avg_dwell_time": [0.0, 4920, 6701, 0],
                "max_dwell_time": [0, 4920, 6701, 0],
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


class InOut(SnakeModel):
    In: List[int]
    Out: List[int]
    EstimatedMaxOccupancy: List[int]
    EstimatedAverageOccupancy: List[float]
    EstimatedLatestOccupancy: List[int]
    Summary: List[Tuple[List[str], List[int], List[int]]]


class InOutLive(LiveReport):
    In: int
    Out: int
    EstimatedMaxOccupancy: int
    EstimatedAverageOccupancy: float
    EstimatedLatestOccupancy: int
    Summary: Tuple[List[str], List[int], List[int]]


class InOutHourly(HourlyReports, InOut):
    class Config:
        schema_extra = {
            "example": [{
                "hours": list(range(0, 23)),
                "in": [0, 0, 0, 0, 0, 1, 1, 2, 2, 3, 0, 7, 0, 3, 3, 0, 0, 0, 2, 1, 0, 0, 0, 0],
                "out": [0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 1, 2, 1, 2, 5, 3, 3, 2, 2, 1, 0, 0, 0, 0],
                "estimated_max_occupancy": [0, 0, 0, 0, 0, 1, 2, 4, 5, 7, 7, 11, 10, 11, 7, 5, 2, 2, 1, 0, 0, 0, 0, 0],
                "estimated_average_occupancy": [0, 0, 0, 0, 0, 0.5, 1.2, 3, 4.2, 7, 6, 8.4, 5, 5, 3, 2, 2, 1, 0.5, 0, 0, 0, 0, 0],
                "estimated_latest_occupancy": [0, 0, 0, 0, 0, 1, 1, 3, 3, 6, 5, 10, 9, 10, 8, 5, 2, 0, 0, 0, 0, 0, 0, 0],
                "summary": [
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 1], [0, 0]],
                    [['Left Door', 'Right Door'], [1, 0], [1, 0]],
                    [['Left Door', 'Right Door'], [0, 2], [0, 0]],
                    [['Left Door', 'Right Door'], [2, 0], [0, 2]],
                    [['Left Door', 'Right Door'], [0, 3], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [1, 0]],
                    [['Left Door', 'Right Door'], [4, 3], [1, 1]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 1]],
                    [['Left Door', 'Right Door'], [0, 3], [2, 0]],
                    [['Left Door', 'Right Door'], [1, 2], [4, 1]],
                    [['Left Door', 'Right Door'], [0, 0], [3, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [3, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [1, 1]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 2]],
                    [['Left Door', 'Right Door'], [0, 0], [1, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]]
                ]
            }]
        }


class InOutDaily(DailyReport, InOut):
    class Config:
        schema_extra = {
            "example": [{
                "dates": ["2020-08-15", "2020-08-16", "2020-08-17", "2020-08-18"],
                "in": [4, 23, 50, 0],
                "out": [4, 23, 50, 0],
                "estimated_max_occupancy": [4, 23, 50, 0],
                "estimated_average_occupancy": [3, 19.5, 40, 0],
                "estimated_latest_occupancy": [0, 0, 0, 0],
                "summary": [
                    [['Left Door', 'Right Door'], [2, 2], [3, 1]],
                    [['Left Door', 'Right Door'], [12, 11], [12, 11]],
                    [['Left Door', 'Right Door'], [42, 8], [8, 42]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]]
                ]
            }]
        }


class InOutWeekly(WeeklyReport, InOut):
    InMax: List[int]
    OutMax: List[int]
    InAvg: List[int]
    OutAvg: List[int]
    class Config:
        schema_extra = {
            "example": [{
                "weeks": ["2020-07-03 2020-07-05", "2020-07-06 2020-07-12", "2020-07-13 2020-07-19", "2020-07-20 2020-07-26"],
                "in": [40, 420, 300, 0],
                "out": [40, 420, 300, 0],
                "in_max": [4, 23, 50, 0],
                "out_max": [4, 23, 50, 0],
                "in_avg": [4, 23, 50, 0],
                "out_avg": [4, 23, 50, 0],
                "estimated_max_occupancy": [40, 420, 300, 0],
                "estimated_average_occupancy": [27.9, 376, 285.4, 0],
                "estimated_latest_occupancy": [0, 0, 0, 0],
                "summary": [
                    [['Left Door', 'Right Door'], [20, 20], [30, 10]],
                    [['Left Door', 'Right Door'], [300, 120], [300, 120]],
                    [['Left Door', 'Right Door'], [150, 150], [150, 150]],
                    [['Left Door', 'Right Door'], [0, 0], [0, 0]]
                ]
            }]
        }
