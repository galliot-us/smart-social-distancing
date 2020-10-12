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


class SourceConfig(SnakeModel):
    VideoPath: Optional[str] = Field(None, example='/repo/data/gard1-4.mp4')
    Tags: Optional[str] = Field(None, example='area1')
    Name: Optional[str] = Field(None, example='Front')

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


class AppConfig(SnakeModel):
    Resolution: Optional[str] = Field(None, example='640,480')
    Encoder: Optional[str] = Field(None,
                                   example='videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast')
    ScreenshotPeriod: Optional[str] = Field(None, example='0')
    ScreenshotS3Bucket: Optional[str] = Field(None, example='my-screenshots-bucket')


class DetectorConfig(SnakeModel):
    Device: Optional[str] = Field(None, example='x86')
    Name: Optional[str] = Field(None, example='openvino')
    ImageSize: Optional[str] = Field(None, example='300,300,3')
    ModelPath: Optional[str] = Field(None, example='')
    ClassID: Optional[str] = Field(None, example='1')
    MinScore: Optional[str] = Field(None, example='0.25')


class PostProcessorConfig(SnakeModel):
    MaxTrackFrame: Optional[str] = Field(None, example='5')
    NMSThreshold: Optional[str] = Field(None, example='0.98')
    DefaultDistMethod: Optional[str] = Field(None, example='CenterPointsDistance')
    DistThreshold: Optional[str] = Field(None, example='150')


class LoggerConfig(SnakeModel):
    Name: Optional[str] = Field(None, example='csv_logger')
    TimeInterval: Optional[str] = Field(None, example='0.5')
    LogDirectory: Optional[str] = Field(None, example='/repo/data/processor/static/data')
    HeatmapResolution: Optional[str] = Field(None, example='150,150')


class ApiConfig(SnakeModel):
    Host: Optional[str] = Field(None, example='0.0.0.0')
    Port: Optional[str] = Field(None, example='8000')


class CoreConfig(SnakeModel):
    Host: Optional[str] = Field(None, example='0.0.0.0')
    QueuePort: Optional[str] = Field(None, example='8010')
    QueueAuthKey: Optional[str] = Field(None, example='shibalba')


class SourceConfigDTO(BaseModel):
    videoPath: str = Field(example='/repo/data/softbio_vid.mp4')
    name: str = Field(example='Front')
    id: str = Field(example='cam1')
    emails: Optional[str] = Field("", example='john@email.com,doe@email.com')
    tags: Optional[str] = Field("", example='kitchen,living_room')
    notifyEveryMinutes: Optional[int] = Field(0, example=15)
    violationThreshold: Optional[int] = Field(0, example=100)
    image: Optional[str] = Field("", example='Base64 image')
    distMethod: Optional[str] = Field("", example='CenterPointsDistance')
    dailyReport: Optional[bool] = Field(False, example=True)


class ConfigDTO(BaseModel):
    cameras: List[SourceConfigDTO]
