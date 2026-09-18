"""Value objects of the IAM bounded context."""
from enum import StrEnum

from shared.domain.exceptions import DomainError


class Role(StrEnum):
    """What an account is allowed to do.

    The set of roles is closed and defined here, in code; name them in the
    ubiquitous language of the platform.
    """

    USER = "ROLE_USER"
    ADMIN = "ROLE_ADMIN"

    @classmethod
    def default(cls) -> "Role":
        """The role an account gets when sign-up names none."""
        return cls.USER

    @classmethod
    def from_name(cls, name: str) -> "Role":
        """Return the role with the given name.

        Raises:
            DomainError: If no role has that name.
        """
        try:
            return cls(name)
        except ValueError:
            raise DomainError(f"Role '{name}' does not exist") from None
