"""Outbound ports of the IAM bounded context.

The application service needs to hash passwords and to issue and read
tokens. It depends on these two interfaces only; ``infrastructure`` supplies
the algorithms, so changing either one never touches a use case.
"""
from abc import ABC, abstractmethod


class HashingService(ABC):
    """Turns a password into a hash and checks a password against one."""

    @abstractmethod
    async def hash(self, password: str) -> str:
        """Return the hash to store for a password."""

    @abstractmethod
    async def verify(self, password: str, password_hash: str) -> bool:
        """Tell whether the password matches the stored hash."""


class TokenService(ABC):
    """Issues bearer tokens and reads them back."""

    @abstractmethod
    def generate_token(self, username: str) -> str:
        """Return a signed token that identifies the username."""

    @abstractmethod
    def get_username_from_token(self, token: str) -> str | None:
        """Return the username a valid token identifies, or ``None``.

        ``None`` covers every way a token can be unusable: malformed, signed
        with another key, or expired.
        """
