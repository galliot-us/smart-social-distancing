from pydantic import BaseModel, Field, validator
from typing import Optional, List
from humps import decamelize
import numpy as np
import cv2 as cv


def to_snake(string):
    return decamelize(string)


class SnakeModel(BaseModel):
    class Config:
        alias_generator = to_snake
        allow_population_by_field_name = True


class EntityConfigDTO(SnakeModel):
    id: str = Field(example='0')
    name: str = Field(example='Kitchen')


class NotificationConfig(SnakeModel):
    violationThreshold: Optional[int] = Field(0, example=100)
    notifyEveryMinutes: Optional[int] = Field(0, example=15)
    emails: Optional[str] = Field("", example='john@email.com,doe@email.com')
    dailyReport: Optional[bool] = Field(False, example=True)


class AreaNotificationConfig(NotificationConfig):
    occupancyThreshold:  Optional[int] = Field(0, example=300)


class AreaConfigDTO(EntityConfigDTO, AreaNotificationConfig):
    cameras: Optional[str] = Field("", example='cam0,cam1')


class SourceConfigDTO(EntityConfigDTO, NotificationConfig):
    videoPath: str = Field(example='/repo/data/softbio_vid.mp4')
    tags: Optional[str] = Field("", example='kitchen,living_room')
    image: Optional[str] = Field("", example='Base64 image')
    distMethod: Optional[str] = Field("", example='CenterPointsDistance')

    @validator('videoPath')
    def video_must_be_valid(cls, video_uri):
        error = False
        input_cap = cv.VideoCapture(video_uri)

        if input_cap.isOpened():
            _, cv_image = input_cap.read()
            if np.shape(cv_image) == ():
                error = True
        else:
            error = True

        input_cap.release()
        if error:
            raise ValueError('Failed to load video. The video URI is not valid')
        else:
            return video_uri


class ConfigDTO(BaseModel):
    cameras: List[SourceConfigDTO]
    areas: List[AreaConfigDTO]
