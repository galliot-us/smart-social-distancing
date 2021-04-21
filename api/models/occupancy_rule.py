from pydantic import Field, validator, root_validator
from typing import List, Optional
from datetime import time

from libs.entities.occupancy_rule import date_before, occ_str_to_time
from .base import SnakeModel

import logging
logger = logging.getLogger(__name__)


class AreaOccupancyRule(SnakeModel):
    days: List[bool]
    start_hour: str = Field(example="08:00")
    start_time: Optional[time] = None
    finish_hour: str = Field(example="12:00")
    finish_time: Optional[time] = None
    max_occupancy: int = Field(example=100)

    @classmethod
    def _valid_time(cls, value: str):
        try:
            t = occ_str_to_time(value)
            if not t:
                return False
            return t
        except:  # noqa
            return False

    @root_validator(pre=True)
    def check_hours(cls, values):
        assert "start_hour" in values, "start_hour is a required field"
        assert "finish_hour" in values, "finish_hour is a required field"
        return values

    @validator('days')
    def days_must_be_seven(cls, days):
        if len(days) != 7:
            raise ValueError("'days' must contain 7 bool values")
        return days

    @validator('start_time', always=True, pre=False)
    def start_hour_must_be_valid(cls, v, values):
        t = cls._valid_time(values['start_hour'])
        if not t:
            raise ValueError("'start_hour' is not in valid format")
        return t

    @validator('finish_time', always=True, pre=False)
    def finish_hour_must_be_valid(cls, v, values):
        t = cls._valid_time(values["finish_hour"])
        if not t:
            raise ValueError("'finish_hour' is not in valid format")
        if "start_hour" in values and not date_before(occ_str_to_time(values["start_hour"]), t):
            raise ValueError("'finish_hour' must be later than 'start_hour'")
        return t

    @validator('max_occupancy')
    def max_occupancy_must_be_positive(cls, max_occupancy):
        if max_occupancy < 0:
            raise ValueError("'max_occupancy' must be > 0")
        return max_occupancy

    def to_store_json(self):
        return {
            "days": list(map(int, self.days)),
            "start_hour": self.start_hour,
            "finish_hour": self.finish_hour,
            "max_occupancy": self.max_occupancy
        }


class OccupancyRuleListDTO(SnakeModel):
    __root__: List[AreaOccupancyRule]

    def __iter__(self):
        return iter(self.__root__)

    def __getitem__(self, item):
        return self.__root__[item]

    @validator('__root__')
    def validate_no_overlaps(cls, the_list):
        for l1 in the_list:
            for l2 in the_list:
                if l1 != l2 and do_overlap(l1, l2):
                    raise ValueError("Occupancy rules must not overlap!")
        return the_list

    def to_store_json(self):
        return {"occupancy_rules": [r.to_store_json() for r in self]}

    @classmethod
    def from_store_json(cls, json_value):
        if "occupancy_rules" not in json_value:
            return []
        objs = [AreaOccupancyRule.parse_obj(v) for v in json_value["occupancy_rules"]]
        return objs


def do_overlap(a: AreaOccupancyRule, b: AreaOccupancyRule):
    for d in range(7):
        if a.days[d] and b.days[d]:
            if (date_before(b.start_time, a.finish_time, strict=True) and
               date_before(a.start_time, b.finish_time, strict=True)):
                return True
    return False
