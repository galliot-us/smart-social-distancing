from pydantic import Field
from typing import List, Optional

from .base import EntityConfigDTO, NotificationConfig, SnakeModel


class AreaNotificationConfig(NotificationConfig):
    occupancyThreshold: Optional[int] = Field(0, example=300)


class AreaConfigDTO(EntityConfigDTO, AreaNotificationConfig):
    cameras: Optional[str] = Field("", example='cam0,cam1')


class AreasListDTO(SnakeModel):
    areas: List[AreaConfigDTO]
