"""In-process event bus.

Application services publish the events an aggregate recorded, after the
transaction that produced them has committed. Handlers subscribe by event type
when the application starts. Delivery is in-process and in order; nothing is
stored, so a handler that fails does not undo the change that raised the event.
"""
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable

from shared.domain.events import DomainEvent

logger = logging.getLogger(__name__)

type EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """Dispatches domain events to the handlers subscribed to their type."""

    def __init__(self) -> None:
        """Initialize the bus with no subscriptions."""
        self._handlers: defaultdict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        """Register a handler for one event type; registering it again has no effect.

        Idempotent because subscriptions happen in the application's lifespan,
        which a test suite may run several times in one process.

        Args:
            event_type (type[DomainEvent]): The event class to listen to.
            handler (EventHandler): Coroutine function called with each event.
        """
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    async def publish(self, events: Iterable[DomainEvent]) -> None:
        """Deliver each event to every handler subscribed to its type.

        A handler that raises is logged and skipped, so that one failing
        reaction never hides the others.

        Args:
            events (Iterable[DomainEvent]): Events pulled from an aggregate.
        """
        for event in events:
            for handler in self._handlers[type(event)]:
                try:
                    await handler(event)
                except Exception:
                    logger.exception("Handler %s failed for %s", handler, event)


event_bus = EventBus()
