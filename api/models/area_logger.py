from pydantic import Field, validator
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class AreaLoggerDTO(OptionalSectionConfig):
    logDirectory: Optional[str] = Field(example="/repo/data/processor/static/data/areas")

    @validator("name")
    def validate_name(cls, value):
        if value != "file_system_logger":
            raise ValueError(f"Not supported logger named: {value}")
        return value


class FileSystemLoggerDTO(OptionalSectionConfig):
    logDirectory: str = Field("/repo/data/processor/static/data/sources",
                              example="/repo/data/processor/static/data/areas")


class AreaLoggerListDTO(SnakeModel):
    areasLoggers: List[AreaLoggerDTO]


def validate_logger(logger: AreaLoggerDTO):
    logger_model = None
    if logger.name == "file_system_logger":
        logger_model = FileSystemLoggerDTO
    # Validate that the specific logger's fields are correctly set
    logger_model(**logger.dict())
