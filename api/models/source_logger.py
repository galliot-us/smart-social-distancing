from pydantic import Field, validator
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class SourceLoggerDTO(OptionalSectionConfig):
    screenshotPeriod: Optional[int] = Field(example=0)
    screenshotS3Bucket: Optional[str] = Field(example="my-screenshot-bucket")
    timeInterval: Optional[float] = Field(example=0.5)
    logDirectory: Optional[str] = Field(example="/repo/data/processor/static/data/sources")
    endpoint: Optional[str] = Field(example="https://my-endpoint/")
    authorization: Optional[str] = Field(example="Bearer Token")
    screenshotsDirectory: Optional[str] = Field(example="/repo/data/processor/static/screenshots")

    @validator("name")
    def validate_name(cls, value):
        if value not in ["file_system_logger", "video_logger", "s3_logger", "web_hook_logger"]:
            raise ValueError(f"Not supported logger named: {value}")
        return value


class VideoLoggerDTO(OptionalSectionConfig):
    pass


class S3LoggerDTO(OptionalSectionConfig):
    screenshotPeriod: int = Field(0, example=0)
    screenshotS3Bucket: str = Field(example="my-screenshot-bucket")


class FileSystemLoggerDTO(OptionalSectionConfig):
    timeInterval: float = Field(0.5, example=0.5)
    logDirectory: str = Field("/repo/data/processor/static/data/sources",
                              example="/repo/data/processor/static/data/sources")
    screenshotPeriod: int = Field(0, example=0)
    screenshotsDirectory: str = Field("", example="/repo/data/processor/static/screenshots")


class WebHookLogger(OptionalSectionConfig):
    endpoint: str = Field("", example="https://my-endpoint/")
    authorization: str = Field("", example="Bearer Token")


class SourceLoggerListDTO(SnakeModel):
    sourcesLoggers: List[SourceLoggerDTO]


def validate_logger(logger: SourceLoggerDTO):
    logger_model = None
    if logger.name == "video_logger":
        logger_model = VideoLoggerDTO
    elif logger.name == "s3_logger":
        logger_model = S3LoggerDTO
    elif logger.name == "file_system_logger":
        logger_model = FileSystemLoggerDTO
    elif logger.name == "web_hook_logger":
        logger_model = WebHookLogger
    logger_model(**logger.dict())
