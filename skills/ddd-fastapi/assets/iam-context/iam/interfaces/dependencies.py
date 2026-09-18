"""Dependency wiring and request authentication of the IAM bounded context.

Besides building its own application service, this module is IAM's public
door for every other context: :func:`get_current_user` authenticates a
request, :data:`CurrentUserDep` hands the caller to a route, and
:func:`require_roles` restricts a route to some roles. Other contexts import
these three and :class:`CurrentUser`, and nothing else from IAM.
"""
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from iam.application.services import UserApplicationService
from iam.domain.value_objects import Role
from iam.infrastructure.hashing import Argon2HashingService
from iam.infrastructure.repositories import SqlAlchemyUserRepository
from iam.infrastructure.tokens import JwtSettings, JwtTokenService
from shared.interfaces.dependencies import SessionDep

bearer_scheme = HTTPBearer(scheme_name="bearerAuth", description="The token returned by sign-in.")

# Read once, at import: a missing or short JWT_SECRET stops the application at
# start-up, with the variable's name in the error, not on the first sign-in.
jwt_settings = JwtSettings()


async def get_user_service(session: SessionDep) -> UserApplicationService:
    """Build the application service on the request's session."""
    return UserApplicationService(
        SqlAlchemyUserRepository(session),
        Argon2HashingService(),
        JwtTokenService(jwt_settings),
        session,
    )


UserServiceDep = Annotated[UserApplicationService, Depends(get_user_service)]


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Who is calling, as other contexts see it.

    Attributes:
        id (int): The account's id; store it to refer to the account.
        username (str): The account's username.
        roles (frozenset[str]): The account's role names.
    """

    id: int
    username: str
    roles: frozenset[str]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)], service: UserServiceDep
) -> CurrentUser:
    """Authenticate the request from its ``Authorization: Bearer`` header.

    Returns:
        CurrentUser: The account the token identifies.

    Raises:
        HTTPException: 401 if the header is missing, the token is invalid or
            expired, or its account no longer exists.
    """
    user = await service.get_user_by_token(credentials.credentials)
    if user is None or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(id=user.id, username=user.username, roles=frozenset(user.roles))


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    """Build a dependency that admits only accounts holding one of the roles.

    Use it on a route or a router: ``dependencies=[Depends(require_roles(Role.ADMIN))]``.

    Raises:
        HTTPException: 403 if the account holds none of the roles.
    """

    async def dependency(user: CurrentUserDep) -> CurrentUser:
        if user.roles.isdisjoint(roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this account")
        return user

    return dependency
