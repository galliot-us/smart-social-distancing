from pydantic import Field, validator
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class SourcePostProcessorDTO(OptionalSectionConfig):
    NMSThreshold: Optional[float] = Field(example=0.98)
    defaultDistMethod: Optional[str] = Field(example="CenterPointsDistance")
    distThreshold: Optional[int] = Field(example=150)

    @validator("name")
    def validate_name(cls, value):
        if value not in ["objects_filtering", "social_distance", "anonymizer"]:
            raise ValueError(f"Not supported post processor named: {value}")
        return value


class ObjectFilteringDTO(OptionalSectionConfig):
    NMSThreshold: float


class SocialDistanceDTO(OptionalSectionConfig):
    defaultDistMethod: str
    distThreshold: int


class AnonymizerDTO(OptionalSectionConfig):
    pass


class SourcePostProcessorListDTO(SnakeModel):
    sourcesPostProcessors: List[SourcePostProcessorDTO]


def validate_post_processor(post_processor: SourcePostProcessorDTO):
    post_processor_model = None
    if post_processor.name == "objects_filtering":
        post_processor_model = ObjectFilteringDTO
    elif post_processor.name == "social_distance":
        post_processor_model = SocialDistanceDTO
    elif post_processor.name == "anonymizer":
        post_processor_model = AnonymizerDTO
    # Validate that the specific post processor's fields are correctly set
    post_processor_model(**post_processor.dict())
