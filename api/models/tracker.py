from pydantic import Field

from .base import SnakeModel


class TrackerDTO(SnakeModel):
    name: str = Field("IOUTracker", example="IOUTracker")
    maxLost: int = Field(5, example=5)
    trackerIOUThreshold: float = Field(0.5, example=0.5)
