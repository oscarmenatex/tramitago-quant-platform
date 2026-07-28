"""Internal storage for dataset availability records."""

from collections.abc import Iterable

from quant_platform.data.availability.dataset_availability_record import (
    DatasetAvailabilityRecord,
)


class DatasetAvailabilityRegistry:
    """Keep one active availability record per dataset version."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], DatasetAvailabilityRecord] = {}

    def register(self, record: DatasetAvailabilityRecord) -> DatasetAvailabilityRecord:
        """Store a new active availability record, rejecting duplicates."""
        key = (record.dataset_id, record.version)
        if key in self._records:
            raise ValueError(
                "An active availability already exists for this dataset version"
            )
        self._records[key] = record
        return record

    def get(self, dataset_id: str, version: str) -> DatasetAvailabilityRecord | None:
        """Return an availability record for one explicit dataset version."""
        return self._records.get((dataset_id, version))

    def exists(self, dataset_id: str, version: str) -> bool:
        """Return whether an explicit dataset version is publicly available."""
        return self.get(dataset_id, version) is not None

    def exists_version(self, dataset_id: str, version: str) -> bool:
        """Return whether a dataset version already has active availability."""
        return (dataset_id, version) in self._records

    def list(self) -> Iterable[DatasetAvailabilityRecord]:
        """Return the active availability records."""
        return tuple(self._records.values())
