"""Research dataset consumption implementation."""

from quant_platform.data.availability import (
    AvailableDataset,
    DatasetAvailabilityAccess,
)


class ResearchDatasetConsumer:
    """Consume only explicitly versioned datasets from the public Data boundary."""

    def __init__(self, access: DatasetAvailabilityAccess) -> None:
        self._access = access

    def load(self, dataset_id: str, version: str) -> AvailableDataset | None:
        """Return the public contract for an available dataset version."""
        return self._access.get(dataset_id, version)

    def load_content(self, dataset_id: str, version: str) -> tuple[object, ...] | None:
        """Resolve content through DatasetAvailabilityAccess without transformation."""
        return self._access.resolve(dataset_id, version)
