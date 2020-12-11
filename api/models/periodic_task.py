from pydantic import Field, validator
from typing import List

from .base import OptionalSectionConfig, SnakeModel


class PeriodicTaskDTO(OptionalSectionConfig):
    liveInterval: int = Field(example=10)

    @validator("name")
    def validate_name(cls, value):
        if value != "metrics":
            raise ValueError(f"Not supported periodic task named: {value}")
        return value


class PeriodicTaskListDTO(SnakeModel):
    periodicTasks: List[PeriodicTaskDTO]
