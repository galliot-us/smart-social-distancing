from pydantic import BaseModel, Field
from typing import Optional
from humps import decamelize


def to_snake(string):
    return decamelize(string)


class SnakeModel(BaseModel):
    class Config:
        alias_generator = to_snake
        allow_population_by_field_name = True


class EntityConfigDTO(SnakeModel):
    id: Optional[str] = Field(example='0')
    name: str = Field(example='Kitchen')


class OptionalSectionConfig(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool
