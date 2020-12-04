from pydantic import Field
from typing import Optional

from .base import SnakeModel


class ClassifierDTO(SnakeModel):
    device: str = Field(example="EdgeTPU")
    name: str = Field(example="OFMClassifier")
    imageSize: str = Field(example="45,45,3")
    modelPath: Optional[str] = Field(example="/repo/data/custom-model")
    minScore: float = Field(0.75, example=0.5)
