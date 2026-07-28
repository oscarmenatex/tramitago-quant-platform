"""Application service that publishes registered datasets as AVAILABLE."""

from datetime import datetime
from uuid import uuid4

from quant_platform.data.access import DatasetAccess
from quant_platform.data.availability.dataset_availability_record import (
    AvailableDataset,
    DatasetAvailabilityRecord,
    DatasetCoverage,
)
from quant_platform.data.availability.dataset_availability_registry import (
    DatasetAvailabilityRegistry,
)
from quant_platform.data.availability.dataset_content_reference import (
    DatasetContentReference,
)
from quant_platform.data.availability.dataset_content_store import DatasetContentStore
from quant_platform.data.models import MarketData

AVAILABLE_STATUS = "AVAILABLE"
REGISTERED_STATUS = "REGISTERED"


class DatasetAvailabilityService:
    """Publish registered dataset versions without changing their metadata."""

    def __init__(
        self,
        dataset_access: DatasetAccess,
        content_store: DatasetContentStore,
        availability_registry: DatasetAvailabilityRegistry,
    ) -> None:
        self._dataset_access = dataset_access
        self._content_store = content_store
        self._availability_registry = availability_registry

    def publish(
        self,
        dataset_id: str,
        version: str,
        content: list[MarketData] | DatasetContentReference,
    ) -> AvailableDataset:
        """Publish one registered dataset version with owned, resolvable content."""
        record = self._dataset_access.get(dataset_id, version)
        if record is None:
            raise ValueError("Dataset version must be registered before publication")
        if record.status != REGISTERED_STATUS:
            raise ValueError("Only REGISTERED datasets can be published as AVAILABLE")
        if self._availability_registry.exists(dataset_id, version):
            raise ValueError(
                "An active availability already exists for this dataset version"
            )

        reference = self._reference_for(dataset_id, version, content)
        resolved_content = self._content_store.resolve(reference)
        if resolved_content is None:
            raise ValueError("content_reference must resolve to registered content")

        availability_record = DatasetAvailabilityRecord(
            dataset_id=record.dataset_id,
            version=record.version,
            content_reference=reference,
            quality_report_id=record.quality_report_id,
            status=AVAILABLE_STATUS,
            created_at=datetime.now(),
            coverage=self._coverage_for(resolved_content),
        )
        self._availability_registry.register(availability_record)
        return self._public_contract(availability_record)

    def resolve(
        self, reference: DatasetContentReference
    ) -> tuple[MarketData, ...] | None:
        """Resolve content only when its exact dataset/version is AVAILABLE."""
        availability = self._availability_registry.get(
            reference.dataset_id, reference.version
        )
        if availability is None or availability.content_reference != reference:
            return None
        return self._content_store.resolve(reference)

    def _reference_for(
        self,
        dataset_id: str,
        version: str,
        content: list[MarketData] | DatasetContentReference,
    ) -> DatasetContentReference:
        if isinstance(content, DatasetContentReference):
            if (
                content.dataset_id != dataset_id
                or content.version != version
                or not self._content_store.owns(content)
            ):
                raise ValueError(
                    "content_reference does not belong to dataset_id/version"
                )
            return content
        reference = DatasetContentReference(
            dataset_id=dataset_id,
            version=version,
            content_id=str(uuid4()),
        )
        self._content_store.register_content(reference, content)
        return reference

    @staticmethod
    def _public_contract(record: DatasetAvailabilityRecord) -> AvailableDataset:
        return AvailableDataset(
            dataset_id=record.dataset_id,
            version=record.version,
            content_reference=record.content_reference,
            quality_reference=record.quality_report_id,
            coverage=record.coverage,
        )

    @staticmethod
    def _coverage_for(content: tuple[MarketData, ...]) -> DatasetCoverage:
        timestamps = [item.timestamp for item in content]
        return DatasetCoverage(
            symbols=tuple(sorted({item.symbol for item in content})),
            start=min(timestamps) if timestamps else None,
            end=max(timestamps) if timestamps else None,
            record_count=len(content),
        )
