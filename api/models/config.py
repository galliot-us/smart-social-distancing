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


class ConfigMetrics(BaseModel):
    social_distancing: bool
    facemask: bool
    occupancy: bool
    in_out: bool


class ConfigInfo(BaseModel):
    version: str
    device: str
    has_been_configured: bool
    metrics: ConfigMetrics

    class Config:
        schema_extra = {
            "example": {
                "version": PROCESSOR_VERSION,
                "device": "device",
                "has_been_configured": True
            }
        }
