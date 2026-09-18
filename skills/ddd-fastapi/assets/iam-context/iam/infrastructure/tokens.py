"""Bearer tokens as signed JWTs, through PyJWT."""
from datetime import UTC, datetime, timedelta

import jwt
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from iam.application.outbound_services import TokenService


class JwtSettings(BaseSettings):
    """Token settings, read from ``JWT_*`` environment variables.

    Attributes:
        secret (str): HMAC key; at least 32 bytes. ``JWT_SECRET``.
        expiration_days (int): How long a token stays valid.
            ``JWT_EXPIRATION_DAYS``.
    """

    model_config = SettingsConfigDict(env_prefix="JWT_", env_file=".env", extra="ignore")

    secret: str = Field(min_length=32)
    expiration_days: int = 7


class JwtTokenService(TokenService):
    """Issues HS256 JWTs whose subject is the username."""

    ALGORITHM = "HS256"

    def __init__(self, settings: JwtSettings) -> None:
        """Initialize the service with its settings."""
        self._settings = settings

    def generate_token(self, username: str) -> str:
        now = datetime.now(UTC)
        claims = {"sub": username, "iat": now, "exp": now + timedelta(days=self._settings.expiration_days)}
        return jwt.encode(claims, self._settings.secret, algorithm=self.ALGORITHM)

    def get_username_from_token(self, token: str) -> str | None:
        try:
            claims = jwt.decode(
                token, self._settings.secret, algorithms=[self.ALGORITHM], options={"require": ["sub", "exp"]}
            )
        except jwt.InvalidTokenError:
            return None
        subject = claims["sub"]
        return subject if isinstance(subject, str) else None
