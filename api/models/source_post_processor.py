from pydantic import Field
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class SourcePostProcessorDTO(OptionalSectionConfig):
    NMSThreshold: Optional[float] = Field(example=0.98)
    defaultDistMethod: Optional[str] = Field(example="CenterPointsDistance")
    distThreshold: Optional[int] = Field(example=150)


class ObjectFilteringDTO(OptionalSectionConfig):
    NMSThreshold: float


class SocialDistanceDTO(OptionalSectionConfig):
    defaultDistMethod: str
    distThreshold: int


class AnonymizerDTO(OptionalSectionConfig):
    pass


class SourcePostProcessorListDTO(SnakeModel):
    sourcesPostProcessors: List[SourcePostProcessorDTO]
