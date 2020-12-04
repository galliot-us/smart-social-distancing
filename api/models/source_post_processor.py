from pydantic import Field
from typing import List, Optional

from .base import SnakeModel


class BaseSourcePostProcessorDTO(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool


class SourcePostProcessorDTO(BaseSourcePostProcessorDTO):
    NMSThreshold: Optional[float] = Field(example=0.98)
    defaultDistMethod: Optional[str] = Field(example="CenterPointsDistance")
    distThreshold: Optional[int] = Field(example=150)


class ObjectFilteringDTO(BaseSourcePostProcessorDTO):
    NMSThreshold: float


class SocialDistanceDTO(BaseSourcePostProcessorDTO):
    defaultDistMethod: str
    distThreshold: int


class AnonymizerDTO(BaseSourcePostProcessorDTO):
    pass


class SourcePostProcessorListDTO(SnakeModel):
    sourcesPostProcessors: List[SourcePostProcessorDTO]
