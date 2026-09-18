"""Repository port of the IAM bounded context."""
from abc import ABC, abstractmethod

from iam.domain.entities import User


class UserRepository(ABC):
    """Collection-like access to :class:`User` aggregates."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Insert or update an account, returning it with its ``id``."""

    @abstractmethod
    async def find_by_id(self, user_id: int) -> User | None:
        """Return the account with the given id, or ``None``."""

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """Return the account with the given username, or ``None``."""

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Tell whether an account uses the username."""

    @abstractmethod
    async def find_all(self) -> list[User]:
        """Return every account, ordered by id."""
