import logging
from enum import Enum
from datetime import date
from pydantic import Field, root_validator
from typing import List, Optional

from .base import SnakeModel

logger = logging.getLogger(__name__)


class ExportDataType(str, Enum):
    raw_data = "raw_data"
    occupancy = "occupancy"
    social_distancing = "social-distancing"
    facemask_usage = "facemask-usage"
    in_out = "in-out"
    dwell_time = "dwell-time"
    all_data = "all_data"


class ExportDTO(SnakeModel):
    areas: Optional[List[str]] = Field([], example=["area1", "area2", "area3"])
    all_areas: Optional[bool] = Field(False, example=True)
    cameras: Optional[List[str]] = Field([], example=["camera1", "camera2"])
    all_cameras: Optional[bool] = Field(False, example=True)
    from_date: Optional[date] = Field(None, example="2020-12-01")
    to_date: Optional[date] = Field(None, example="2020-12-02")
    data_types: List[ExportDataType] = Field(example=["all_data"])

    @root_validator
    def validate_dates(cls, values):
        from_date = values.get("from_date")
        to_date = values.get("to_date")
        if not any([from_date, to_date]):
            # No dates were sent, export data from the beginning of the times
            return values
        elif not from_date or not to_date:
            # Only one date was sent. It's an invalid range
            raise ValueError("Invalid range of dates")
        elif from_date > to_date:
            raise ValueError("Invalid range of dates")
        return values

    @root_validator
    def validate_entities(cls, values):
        if not any([values.get("areas"), values.get("all_areas"), values.get("cameras"),
                    values.get("all_cameras")]):
            logger.info("No cameras or areas were provided.")
            raise ValueError("No cameras or areas were provided. You need to provide unless one camera or "
                             "area to call the export endpoint.")
        return values
