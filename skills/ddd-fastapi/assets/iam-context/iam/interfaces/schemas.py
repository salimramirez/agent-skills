"""Request and response schemas of the IAM REST API."""
from pydantic import BaseModel, Field

from iam.domain.entities import User


class SignUpRequest(BaseModel):
    """Body of ``POST /api/v1/authentication/sign-up``."""

    username: str = Field(min_length=3, max_length=50, examples=["ana"])
    password: str = Field(min_length=8, max_length=128, examples=["s3cret-pass"])
    roles: list[str] = Field(default_factory=list, examples=[["ROLE_USER"]])


class SignInRequest(BaseModel):
    """Body of ``POST /api/v1/authentication/sign-in``."""

    username: str = Field(examples=["ana"])
    password: str = Field(examples=["s3cret-pass"])


class UserResponse(BaseModel):
    """An account as the API returns it; never the password hash."""

    id: int
    username: str
    roles: list[str]

    @classmethod
    def from_entity(cls, user: User) -> "UserResponse":
        """Build the response from the aggregate."""
        assert user.id is not None
        return cls(id=user.id, username=user.username, roles=sorted(user.roles))


class AuthenticatedUserResponse(BaseModel):
    """The result of a successful sign-in."""

    id: int
    username: str
    token: str

    @classmethod
    def from_entity(cls, user: User, token: str) -> "AuthenticatedUserResponse":
        """Build the response from the account and its token."""
        assert user.id is not None
        return cls(id=user.id, username=user.username, token=token)
