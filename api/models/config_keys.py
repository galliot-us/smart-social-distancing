from pydantic import BaseModel, Field, ValidationError, validator
from typing import Optional
from humps import decamelize
import numpy as np
import cv2 as cv


def to_snake(string):
    return decamelize(string)


class SnakeModel(BaseModel):
  class Config:
      alias_generator = to_snake
      allow_population_by_field_name = True


class AppConfig(SnakeModel):
    VideoPath: Optional[str] = Field(None, example='/repo/data/gard1-4.mp4')
    Resolution: Optional[str] = Field(None, example='640,480')
    Encoder: Optional[str] = Field(None, example='videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast')

    @validator('VideoPath')
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


class DetectorConfig(SnakeModel):
    Device: Optional[str] = Field(None, example='x86')
    Name: Optional[str] = Field(None, example='mobilenet_ssd_v2')
    ImageSize: Optional[str] = Field(None, example='300,300,3')
    ModelPath: Optional[str] = Field(None, example='')
    ClassID: Optional[str] = Field(None, example='1')
    MinScore: Optional[str] = Field(None, example='0.25')


class PostProcessorConfig(SnakeModel):
    MaxTrackFrame: Optional[str] = Field(None, example='5')
    NMSThreshold: Optional[str] = Field(None, example='0.98')
    DistThreshold: Optional[str] = Field(None, example='150')
    DistMethod: Optional[str] = Field(None, example='CenterPointsDistance')


class LoggerConfig(SnakeModel):
    Name: Optional[str] = Field(None, example='csv_logger')
    TimeInterval: Optional[str] = Field(None, example='0.5')
    LogDirectory: Optional[str] = Field(None, example='/repo/data/processor/static/data')


class ApiConfig(BaseModel):
    Host: Optional[str] = Field(None, example='0.0.0.0')
    Port: Optional[str] = Field(None, example='8000')


class CoreConfig(SnakeModel):
    Host: Optional[str] = Field(None, example='0.0.0.0')
    QueuePort: Optional[str] = Field(None, example='8010')
    QueueAuthKey: Optional[str] = Field(None, example='shibalba')


class Config(SnakeModel):
    App: Optional[AppConfig]
    Detector: Optional[DetectorConfig]
    PostProcessor: Optional[PostProcessorConfig]
    Logger: Optional[LoggerConfig]
    CORE: Optional[CoreConfig]
    API:  Optional[ApiConfig]
