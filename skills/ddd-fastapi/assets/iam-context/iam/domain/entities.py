"""Aggregates of the IAM bounded context."""
from collections.abc import Iterable

from iam.domain.value_objects import Role
from shared.domain.entities import AggregateRoot
from shared.domain.exceptions import DomainError


class User(AggregateRoot):
    """An account that can sign in.

    Attributes:
        id (int | None): Identity assigned when the user is first saved.
        username (str): Unique name used to sign in.
        password_hash (str): The hashed password; the plain one is never kept.
        roles (frozenset[Role]): What the account may do; never empty.
    """

    def __init__(self, username: str, password_hash: str, roles: Iterable[Role] = (), id: int | None = None) -> None:
        """Initialize an account; with no roles it gets the default one.

        Raises:
            DomainError: If the username is blank.
        """
        super().__init__()
        if not username.strip():
            raise DomainError("Username must not be blank")
        self._id = id
        self._username = username.strip()
        self._password_hash = password_hash
        self._roles = frozenset(roles) or frozenset({Role.default()})

    @property
    def id(self) -> int | None:
        """Identity assigned by the first save; ``None`` before it."""
        return self._id

    @property
    def username(self) -> str:
        """Unique name used to sign in."""
        return self._username

    @property
    def password_hash(self) -> str:
        """The hashed password."""
        return self._password_hash

    @property
    def roles(self) -> frozenset[Role]:
        """What the account may do."""
        return self._roles

    def grant(self, role: Role) -> None:
        """Give the account one more role."""
        self._roles = self._roles | {role}

    def has_any_role(self, *roles: Role) -> bool:
        """Tell whether the account holds at least one of the roles."""
        return not self._roles.isdisjoint(roles)
