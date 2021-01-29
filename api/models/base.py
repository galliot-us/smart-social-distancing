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


class NotificationConfig(SnakeModel):
    violationThreshold: Optional[int] = Field(0, example=100)
    notifyEveryMinutes: Optional[int] = Field(0, example=15)
    emails: Optional[str] = Field("", example='john@email.com,doe@email.com')
    enableSlackNotifications: Optional[bool] = Field(False, example=False)
    dailyReport: Optional[bool] = Field(False, example=True)
    dailyReportTime: Optional[str] = Field('06:00', example='06:00')


class OptionalSectionConfig(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool
