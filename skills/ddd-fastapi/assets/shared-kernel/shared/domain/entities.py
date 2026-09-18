"""Aggregate root base class.

Every aggregate root extends :class:`AggregateRoot` so that it can record
domain events while it enforces its rules. The application service pulls them
after the transaction commits and hands them to the event bus.
"""
from shared.domain.events import DomainEvent


class AggregateRoot:
    """Base class for aggregate roots.

    Holds the domain events raised since the aggregate was loaded or created.
    It carries no identity and no persistence concern: each aggregate declares
    its own ``id``.
    """

    def __init__(self) -> None:
        """Initialize the aggregate with no pending events."""
        self._events: list[DomainEvent] = []

    def record_event(self, event: DomainEvent) -> None:
        """Record a domain event raised by this aggregate.

        Args:
            event (DomainEvent): The fact to publish once the change is saved.
        """
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return the pending domain events and clear them.

        Returns:
            list[DomainEvent]: The events in the order they were recorded.
        """
        events, self._events = self._events, []
        return events
