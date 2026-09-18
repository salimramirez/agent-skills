"""Unit-of-work port.

The application layer owns the transaction: a command method changes an
aggregate, saves it through its repository, and then commits. This protocol is
all it needs to know about the transaction; an ``AsyncSession`` satisfies it
as it is, so no adapter class is needed.
"""
from typing import Protocol


class UnitOfWork(Protocol):
    """The transaction boundary an application service commits or rolls back."""

    async def commit(self) -> None:
        """Make every change of the current transaction durable."""
        ...

    async def rollback(self) -> None:
        """Discard every change of the current transaction."""
        ...
