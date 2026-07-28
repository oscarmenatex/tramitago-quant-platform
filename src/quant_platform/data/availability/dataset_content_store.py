"""In-memory content store for dataset availability MVP."""

from typing import Optional

from quant_platform.data.models import MarketData
from quant_platform.data.availability.dataset_content_reference import (
    DatasetContentReference,
)


class DatasetContentStore:
    """Store dataset content separately from registry metadata."""

    def __init__(self) -> None:
        self._content: dict[DatasetContentReference, tuple[MarketData, ...]] = {}

    def register_content(
        self, reference: DatasetContentReference, content: list[MarketData]
    ) -> None:
        """Associate content with a resolvable reference."""
        if reference in self._content:
            raise ValueError("content reference is already registered")
        if any(item.content_id == reference.content_id for item in self._content):
            raise ValueError("content_id is already associated with another dataset")
        self._content[reference] = tuple(content)

    def resolve(
        self, reference: DatasetContentReference
    ) -> Optional[tuple[MarketData, ...]]:
        """Resolve content by reference without modifying it."""
        stored = self._content.get(reference)
        if stored is None:
            return None
        return stored

    def owns(self, reference: DatasetContentReference) -> bool:
        """Return whether this exact reference owns registered content."""
        return reference in self._content
