from pydantic import Field
from typing import List, Optional

from .base import OptionalSectionConfig, SnakeModel


class AreaLoggerDTO(OptionalSectionConfig):
    logDirectory: Optional[str] = Field(example="/repo/data/processor/static/data/areas")


class FileSystemLoggerDTO(OptionalSectionConfig):
    logDirectory: str = Field("/repo/data/processor/static/data/sources",
                              example="/repo/data/processor/static/data/areas")


class AreaLoggerListDTO(SnakeModel):
    areasLoggers: List[AreaLoggerDTO]
