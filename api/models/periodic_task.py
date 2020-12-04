from pydantic import Field
from typing import List

from .base import SnakeModel


class PeriodicTaskDTO(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool


class PeriodicTaskListDTO(SnakeModel):
    periodicTasks: List[PeriodicTaskDTO]
