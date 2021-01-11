from pydantic import Field
from typing import Optional

from .base import SnakeModel


class AppDTO(SnakeModel):
    hasBeenConfigured: bool = Field(False)
    resolution: str = Field("640,480")
    encoder: str = Field("videoconvert ! video/x-raw,format=I420 ! x264enc speed-preset=ultrafast")
    maxProcesses: int = Field(1)
    dashboardURL: str = Field("http://0.0.0.0:8000")
    slackChannel: Optional[str] = Field("", example="lanthorn-notifications")
    occupancyAlertsMinInterval: int = Field(0, example=180)
    maxThreadRestarts: int = Field(5)
    globalReportingEmails: Optional[str] = Field("", example="email@email,email2@email")
    globalReportTime: str = Field("06:00")
    dailyGlobalReport: bool = Field(False)
    weeklyGlobalReport: bool = Field(False)
    heatmapResolution = Field("150,150")
    logPerformance: bool = Field(False)
