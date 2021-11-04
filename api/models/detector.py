from pydantic import Field
from typing import Optional

from .base import SnakeModel


class DetectorDTO(SnakeModel):
    device: str = Field(example="EdgeTPU")
    name: str = Field(example="posenet")
    imageSize: str = Field(example="641,481,3")
    modelPath: Optional[str] = Field(example="/repo/data/custom-model")
    classID: str = Field(example=0)
    minScore: float = Field(0.25, example=0.5)
    deviceId: Optional[str] = Field(example="usb:0")
