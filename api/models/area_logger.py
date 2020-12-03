from pydantic import Field
from typing import List, Optional

from .config_keys import SnakeModel


class BaseAreaLoggerDTO(SnakeModel):
    name: str = Field(example="objects_filtering")
    enabled: bool


class AreaLoggerDTO(BaseAreaLoggerDTO):
    logDirectory: Optional[str] = Field(example="/repo/data/processor/static/data/areas")


class FileSystemLoggerDTO(BaseAreaLoggerDTO):
    logDirectory: str = Field("/repo/data/processor/static/data/sources",
                              example="/repo/data/processor/static/data/areas")


class AreaLoggerListDTO(SnakeModel):
    areasLoggers: List[AreaLoggerDTO]
