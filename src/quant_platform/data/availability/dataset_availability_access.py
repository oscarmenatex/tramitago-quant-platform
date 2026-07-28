"""Public, read-only availability boundary for internal consumers."""

from quant_platform.data.availability.dataset_availability_record import (
    AvailableDataset,
    DatasetAvailabilityRecord,
)
from quant_platform.data.availability.dataset_availability_registry import (
    DatasetAvailabilityRegistry,
)
from quant_platform.data.availability.dataset_content_store import DatasetContentStore
from quant_platform.data.models import MarketData


class DatasetAvailabilityAccess:
    """Expose stable available datasets and their exact versioned content."""

    def __init__(
        self, registry: DatasetAvailabilityRegistry, content_store: DatasetContentStore
    ) -> None:
        self._availability_registry = registry
        self._content_store = content_store

    def get(self, dataset_id: str, version: str) -> AvailableDataset | None:
        """Get one explicitly requested available dataset version."""
        record = self._availability_registry.get(dataset_id, version)
        return self._public_contract(record) if record is not None else None

    def exists(self, dataset_id: str, version: str) -> bool:
        """Return whether an explicit dataset version is publicly available."""
        return self._availability_registry.exists(dataset_id, version)

    def list(self) -> tuple[AvailableDataset, ...]:
        """List all publicly available dataset versions."""
        return tuple(
            self._public_contract(record)
            for record in self._availability_registry.list()
        )

    def resolve(self, dataset_id: str, version: str) -> tuple[MarketData, ...] | None:
        """Resolve content only for the requested available dataset version."""
        available = self.get(dataset_id, version)
        if available is None:
            return None
        return self._content_store.resolve(available.content_reference)

    @staticmethod
    def _public_contract(record: DatasetAvailabilityRecord) -> AvailableDataset:
        return AvailableDataset(
            dataset_id=record.dataset_id,
            version=record.version,
            content_reference=record.content_reference,
            quality_reference=record.quality_report_id,
            coverage=record.coverage,
        )
