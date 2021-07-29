from pydantic import BaseModel, Field
from typing import List, Optional

from constants import PROCESSOR_VERSION

from .app import AppDTO
from .api import ApiDTO
from .base import SnakeModel
from .camera import CameraDTO
from .classifier import ClassifierDTO
from .core import CoreDTO
from .detector import DetectorDTO
from .periodic_task import PeriodicTaskDTO
from .source_logger import SourceLoggerDTO
from .source_post_processor import SourcePostProcessorDTO
from .tracker import TrackerDTO


class ConfigDTO(SnakeModel):
    app: AppDTO
    api: ApiDTO
    core: CoreDTO
    cameras: List[CameraDTO]
    detector: DetectorDTO
    classifier: Optional[ClassifierDTO]
    tracker: TrackerDTO
    sourcePostProcessors: List[SourcePostProcessorDTO]
    sourceLoggers: List[SourceLoggerDTO]
    periodicTasks: Optional[List[PeriodicTaskDTO]] = []


class GlobalReportingEmailsInfo(BaseModel):
    emails: Optional[str] = Field("", example='john@email.com,doe@email.com')
    time: Optional[str] = Field("06:00")
    daily: Optional[bool] = Field(False, example=True)
    weekly: Optional[bool] = Field(False, example=True)

    class Config:
        schema_extra = {
            "example": {
                "emails": "john@email.com,doe@email.com",
                "time": "06:00",
                "daily": True,
                "weekly": True
            }
        }


class ConfigInfo(BaseModel):
    version: str
    device: str
    has_been_configured: bool

    class Config:
        schema_extra = {
            "example": {
                "version": PROCESSOR_VERSION,
                "device": "device",
                "has_been_configured": True
            }
        }
