"""Domain exceptions of the IAM bounded context."""
from shared.domain.exceptions import ConflictError, DomainError, NotFoundError


class InvalidCredentialsError(DomainError):
    """The username or the password is wrong.

    One exception for both cases, so a response never tells which one it was.
    """

    def __init__(self) -> None:
        """Build the fixed message."""
        super().__init__("Invalid username or password")


class UsernameTakenError(ConflictError):
    """Another account already uses the username."""

    def __init__(self, username: str) -> None:
        """Build the message from the username that is taken."""
        super().__init__(f"Username {username} is already taken")


class UserNotFoundError(NotFoundError):
    """No account has the given id."""

    def __init__(self, user_id: int) -> None:
        """Build the message from the id that was not found."""
        super().__init__(f"User with id {user_id} not found")
