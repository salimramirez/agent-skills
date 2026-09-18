"""SQLAlchemy implementation of the IAM repository port."""
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from iam.domain.entities import User
from iam.domain.repositories import UserRepository
from iam.domain.value_objects import Role
from iam.infrastructure.models import UserModel, UserRoleModel


class SqlAlchemyUserRepository(UserRepository):
    """Stores :class:`User` aggregates in ``users`` and ``user_roles``."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository on the request's session."""
        self._session = session

    async def save(self, user: User) -> User:
        model = await self._session.merge(self._to_model(user))
        await self._session.flush()
        return self._to_entity(model)

    async def find_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    async def find_by_username(self, username: str) -> User | None:
        model = await self._session.scalar(select(UserModel).where(UserModel.username == username))
        return self._to_entity(model) if model else None

    async def exists_by_username(self, username: str) -> bool:
        return bool(await self._session.scalar(select(exists().where(UserModel.username == username))))

    async def find_all(self) -> list[User]:
        models = await self._session.scalars(select(UserModel).order_by(UserModel.id))
        return [self._to_entity(model) for model in models]

    @staticmethod
    def _to_model(user: User) -> UserModel:
        return UserModel(
            id=user.id,
            username=user.username,
            password_hash=user.password_hash,
            roles=[UserRoleModel(user_id=user.id, role=role.value) for role in sorted(user.roles)],
        )

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(model.username, model.password_hash, [Role(row.role) for row in model.roles], id=model.id)
