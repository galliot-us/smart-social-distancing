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
    VideoPath: Optional[str] = Field(None, example='/repo/data/TownCentreXVID.avi')
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


class DETECTOR(BaseModel):
     Device: Optional[str]
     Name: Optional[str]
     ImageSize: Optional[str]
     ModelPath: Optional[str]
     ClassID: Optional[str]
     MinScore: Optional[str]

class CORE_(BaseModel):
    Host: Optional[str]
    QueuePort: Optional[str]
    QueueAuthKey: Optional[str]

class POSTPROCESSOR(BaseModel):
    MaxTrackFrame: Optional[str]
    NMSThreshold: Optional[str]
    DistThreshold: Optional[str]
    DistMethod: Optional[str]

class LOGGER(BaseModel):
    Name: Optional[str]
    TimeInterval: Optional[str]
    LogDirectory: Optional[str]

class API_(BaseModel):
    Host: Optional[str]
    Port: Optional[str]

class Config(SnakeModel):
    App: Optional[AppConfig]
    Detector: Optional[DETECTOR]
    PostProcessor: Optional[POSTPROCESSOR]
    Logger: Optional[LOGGER]
    API:  Optional[API_]
    CORE: Optional[CORE_]


class ConfigRequest(BaseModel):
    save_file: Optional[bool] = Field(False)
    config: Config
