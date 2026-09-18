"""REST routes of the IAM bounded context.

``authentication_router`` is public: it is how a client gets a token.
``users_router`` and ``roles_router`` need one, like every other context's.
"""
from fastapi import APIRouter, status

from iam.domain.value_objects import Role
from iam.interfaces.dependencies import UserServiceDep
from iam.interfaces.schemas import AuthenticatedUserResponse, SignInRequest, SignUpRequest, UserResponse
from shared.interfaces.schemas import error_responses

authentication_router = APIRouter(prefix="/api/v1/authentication", tags=["Authentication"])
users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])
roles_router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])


@authentication_router.post("/sign-up", status_code=status.HTTP_201_CREATED, responses=error_responses(400, 409))
async def sign_up(request: SignUpRequest, service: UserServiceDep) -> UserResponse:
    """Create an account."""
    user = await service.sign_up(request.username, request.password, request.roles)
    return UserResponse.from_entity(user)


@authentication_router.post("/sign-in", responses=error_responses(401))
async def sign_in(request: SignInRequest, service: UserServiceDep) -> AuthenticatedUserResponse:
    """Check the credentials and return a bearer token."""
    user, token = await service.sign_in(request.username, request.password)
    return AuthenticatedUserResponse.from_entity(user, token)


@users_router.get("")
async def get_all_users(service: UserServiceDep) -> list[UserResponse]:
    """List every account."""
    return [UserResponse.from_entity(user) for user in await service.get_all_users()]


@users_router.get("/{user_id}", responses=error_responses(404))
async def get_user_by_id(user_id: int, service: UserServiceDep) -> UserResponse:
    """Get one account."""
    return UserResponse.from_entity(await service.get_user_by_id(user_id))


@roles_router.get("")
async def get_all_roles() -> list[str]:
    """List the roles an account can hold."""
    return [role.value for role in Role]
