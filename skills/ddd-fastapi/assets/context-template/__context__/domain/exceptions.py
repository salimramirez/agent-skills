"""Domain exceptions of the __Context_title__ bounded context."""
from shared.domain.exceptions import NotFoundError


class __Entity__NotFoundError(NotFoundError):
    """No __entity_words__ has the given id."""

    def __init__(self, __entity___id: int) -> None:
        """Build the message from the id that was not found.

        Args:
            __entity___id (int): The id that was looked up.
        """
        super().__init__(f"__Entity_sentence__ with id {__entity___id} not found")
