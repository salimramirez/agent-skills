"""ORM models of the __Context_title__ bounded context.

These classes describe tables, nothing else. Only the repository in this
package imports them; the domain and application layers never see them.
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.infrastructure.models import AuditableModel, Base


class __Entity__Model(AuditableModel, Base):
    """The ``__entities__`` table."""

    __tablename__ = "__entities__"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
