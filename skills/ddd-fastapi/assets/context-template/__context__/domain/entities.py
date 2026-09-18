"""Aggregates of the __Context_title__ bounded context."""
from shared.domain.entities import AggregateRoot
from shared.domain.exceptions import DomainError


class __Entity__(AggregateRoot):
    """A __entity_words__.

    ``name`` is a placeholder: replace it with the real attributes, named as the
    domain experts name them, and put every rule that protects them in a method
    of this class.

    Attributes:
        id (int | None): Identity assigned when the __entity_words__ is first saved.
        name (str): Placeholder attribute.
    """

    def __init__(self, name: str, id: int | None = None) -> None:
        """Initialize a __entity_words__.

        Args:
            name (str): Must not be blank.
            id (int | None): Persistence identity; ``None`` until saved.

        Raises:
            DomainError: If the name is blank.
        """
        super().__init__()
        self._id = id
        self._name = self._require_name(name)

    @property
    def id(self) -> int | None:
        """Identity assigned by the first save; ``None`` before it."""
        return self._id

    @property
    def name(self) -> str:
        """Placeholder attribute."""
        return self._name

    def rename(self, name: str) -> None:
        """Replace the name.

        Raises:
            DomainError: If the name is blank.
        """
        self._name = self._require_name(name)

    @staticmethod
    def _require_name(name: str) -> str:
        if not name.strip():
            raise DomainError("__Entity_sentence__ name must not be blank")
        return name.strip()
