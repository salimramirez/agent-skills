"""Domain event base type.

A domain event records something that happened in the domain that other code
may need to react to. Events are immutable facts named in the past tense
(``OrderPlaced``, not ``PlaceOrder``).
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Base class for every domain event.

    Subclasses are frozen dataclasses that add the facts the event carries.

    Attributes:
        occurred_at (datetime): UTC instant the event was raised.
    """

    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
