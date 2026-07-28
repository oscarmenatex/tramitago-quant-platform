"""Internal dataset access implementation."""

from typing import Optional

from quant_platform.data.registry import DatasetRegistry
from quant_platform.data.registry.dataset_record import DatasetRecord


class DatasetAccess:
    """Provide internal access to registered dataset metadata."""

    def __init__(self, registry: DatasetRegistry) -> None:
        self._registry = registry

    def get(self, dataset_id: str, version: str) -> Optional[DatasetRecord]:
        """Return a registered DatasetRecord for an explicit version."""
        return self._registry.get(dataset_id, version)
