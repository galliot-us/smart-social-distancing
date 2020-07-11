from pydantic import BaseModel
from typing import Optional


class APP(BaseModel):
    VideoPath: Optional[str]
    Host: Optional[str]=None
    Port: Optional[str] 
    Resolution: Optional[str]
    Encoder: Optional[str]

class DETECTOR(BaseModel):
     Device: Optional[str]
     Name: Optional[str]
     ImageSize: Optional[str]
     ModelPath: Optional[str]
     ClassID: Optional[str]
     MinScore: Optional[str]


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

class Config(BaseModel):
    App: Optional[APP]
    Detector: Optional[DETECTOR]
    PostProcessor: Optional[POSTPROCESSOR]
    Logger: Optional[LOGGER]
    API:  Optional[API_]

