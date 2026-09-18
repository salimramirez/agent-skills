"""Domain exception hierarchy.

Every failure the domain can name extends :class:`DomainError`. The classes
here say *what kind* of failure it is; the interface layer decides which HTTP
status each kind becomes. No status code appears in the domain.
"""


class DomainError(Exception):
    """A domain rule rejected the input.

    Raised for values that cannot be right: a blank name, a negative quantity,
    a price in the wrong currency. The message is written for the API client.
    """


class ConflictError(DomainError):
    """The current state of the domain forbids the operation.

    Raised for a state transition that is not allowed (placing an order that is
    already placed) and for a uniqueness rule (an email already registered).
    """


class NotFoundError(DomainError):
    """A named aggregate does not exist."""
