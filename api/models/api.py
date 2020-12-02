from pydantic import Field
from typing import Optional

from .config_keys import SnakeModel


class ApiDTO(SnakeModel):
    host: str = Field("0.0.0.0")
    port: int = Field(8000)
    SSLEnabled: Optional[bool] = Field(False)
    SSLCertificateFile: Optional[str] = Field("", example="/repo/certs/0_0_0_0.crt")
    SSLKeyFile: Optional[str] = Field("", example="/repo/certs/0_0_0_0.key")
