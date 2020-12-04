from typing import List

from .base import OptionalSectionConfig, SnakeModel


class PeriodicTaskDTO(OptionalSectionConfig):
    pass


class PeriodicTaskListDTO(SnakeModel):
    periodicTasks: List[PeriodicTaskDTO]
