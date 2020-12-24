from .base import SnakeModel


class AuthDTO(SnakeModel):
    user: str
    password: str


class Token(SnakeModel):
    token: str
