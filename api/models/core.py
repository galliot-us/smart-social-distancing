from pydantic import Field

from .base import SnakeModel


class CoreDTO(SnakeModel):
    host: str = Field("0.0.0.0", example="0.0.0.0")
    queuePort: int = Field(8010, example=8010)
    queueAuthKey: str = Field("", example="shibalba")
