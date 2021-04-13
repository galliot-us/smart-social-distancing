from pydantic import Field
from typing import List, Optional

from .base import EntityConfigDTO, NotificationConfig, SnakeModel
from .occupancy_rule import OccupancyRuleListDTO


class AreaNotificationConfig(NotificationConfig):
    occupancyThreshold: Optional[int] = Field(0, example=300)


class AreaConfigDTO(EntityConfigDTO, AreaNotificationConfig):
    cameras: Optional[str] = Field("", example='cam0,cam1')
    occupancy_rules: Optional[OccupancyRuleListDTO] = Field([], example=[])


class AreasListDTO(SnakeModel):
    areas: List[AreaConfigDTO]
