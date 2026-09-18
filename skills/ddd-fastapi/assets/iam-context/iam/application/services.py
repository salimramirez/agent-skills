"""Application service of the IAM bounded context."""
from iam.application.outbound_services import HashingService, TokenService
from iam.domain.entities import User
from iam.domain.exceptions import InvalidCredentialsError, UsernameTakenError, UserNotFoundError
from iam.domain.repositories import UserRepository
from iam.domain.value_objects import Role
from shared.application.unit_of_work import UnitOfWork


class UserApplicationService:
    """Use cases that create accounts, sign them in and read them."""

    def __init__(
        self,
        user_repository: UserRepository,
        hashing_service: HashingService,
        token_service: TokenService,
        unit_of_work: UnitOfWork,
    ) -> None:
        """Initialize the service with its collaborators."""
        self._users = user_repository
        self._hashing = hashing_service
        self._tokens = token_service
        self._unit_of_work = unit_of_work

    async def sign_up(self, username: str, password: str, role_names: list[str]) -> User:
        """Create an account.

        Args:
            username (str): Unique name to sign in with.
            password (str): The plain password; only its hash is stored.
            role_names (list[str]): Roles to grant; the default one if empty.

        Returns:
            User: The stored account.

        Raises:
            UsernameTakenError: If the username is in use.
            DomainError: If a role does not exist or the username is blank.
        """
        if await self._users.exists_by_username(username):
            raise UsernameTakenError(username)
        roles = [Role.from_name(name) for name in role_names]
        user = User(username, await self._hashing.hash(password), roles)
        user = await self._users.save(user)
        await self._unit_of_work.commit()
        return user

    async def sign_in(self, username: str, password: str) -> tuple[User, str]:
        """Check the credentials and issue a token.

        Returns:
            tuple[User, str]: The account and its bearer token.

        Raises:
            InvalidCredentialsError: If the username or the password is wrong.
        """
        user = await self._users.find_by_username(username)
        if user is None or not await self._hashing.verify(password, user.password_hash):
            raise InvalidCredentialsError()
        return user, self._tokens.generate_token(user.username)

    async def get_user_by_token(self, token: str) -> User | None:
        """Return the account a bearer token identifies, or ``None``."""
        username = self._tokens.get_username_from_token(token)
        return await self._users.find_by_username(username) if username else None

    async def get_user_by_id(self, user_id: int) -> User:
        """Return one account.

        Raises:
            UserNotFoundError: If no account has the id.
        """
        user = await self._users.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def get_all_users(self) -> list[User]:
        """Return every account, ordered by id."""
        return await self._users.find_all()
