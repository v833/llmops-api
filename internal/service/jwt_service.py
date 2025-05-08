import os
from injector import inject
from dataclasses import dataclass
from typing import Any
import jwt


@inject
@dataclass
class JwtService:
    """JWT服务"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        secret_key = os.getenv("JWT_SECRET_KEY")
        jwt.encode(payload, secret_key, algorithm="HS256")
        pass

    @classmethod
    def parse_token(cls, token) -> dict[str, Any]:
        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
