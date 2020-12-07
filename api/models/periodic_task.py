from pydantic import validator
from typing import List

from .base import OptionalSectionConfig, SnakeModel


class PeriodicTaskDTO(OptionalSectionConfig):

    @validator("name")
    def validate_name(cls, value):
        if value != "reports":
            raise ValueError(f"Not supported periodic task named: {value}")
        return value


class PeriodicTaskListDTO(SnakeModel):
    periodicTasks: List[PeriodicTaskDTO]
