from pydantic import Field
from typing import List, Optional

from .base import SnakeModel


class BaseSourceLoggerDTO(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool


class SourceLoggerDTO(BaseSourceLoggerDTO):
    screenshotPeriod: Optional[int] = Field(example=0)
    screenshotS3Bucket: Optional[str] = Field(example="my-screenshot-bucket")
    timeInterval: Optional[float] = Field(example=0.5)
    logDirectory: Optional[str] = Field(example="/repo/data/processor/static/data/sources")
    endpoint: Optional[str] = Field(example="https://my-endpoint/")


class VideoLoggerDTO(BaseSourceLoggerDTO):
    pass


class S3LoggerDTO(BaseSourceLoggerDTO):
    screenshotPeriod: int = Field(0, example=0)
    screenshotS3Bucket: str = Field(example="my-screenshot-bucket")


class FileSystemLoggerDTO(BaseSourceLoggerDTO):
    timeInterval: float = Field(0.5, example=0.5)
    logDirectory: str = Field("/repo/data/processor/static/data/sources",
                              example="/repo/data/processor/static/data/sources")
    screenshotPeriod: int = Field(0, example=0)


class WebHookLogger(BaseSourceLoggerDTO):
    endpoint: str = Field("", example="https://my-endpoint/")


class SourceLoggerListDTO(SnakeModel):
    sourcesLoggers: List[SourceLoggerDTO]
