"""ORM models of the IAM bounded context."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.infrastructure.models import AuditableModel, Base


class UserModel(AuditableModel, Base):
    """The ``users`` table."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    roles: Mapped[list["UserRoleModel"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class UserRoleModel(Base):
    """The ``user_roles`` table: one row per role an account holds."""

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(30), primary_key=True)
