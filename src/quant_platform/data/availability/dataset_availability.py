"""Dataset availability service for resolving content."""

from typing import Optional
from quant_platform.data.access import DatasetAccess
from quant_platform.data.availability.dataset_availability_registry import (
    DatasetAvailabilityRegistry,
)
from quant_platform.data.availability.dataset_availability_service import (
    DatasetAvailabilityService,
)
from quant_platform.data.availability.dataset_content_reference import (
    DatasetContentReference,
)
from quant_platform.data.availability.dataset_content_store import DatasetContentStore
from quant_platform.data.models import MarketData
from quant_platform.data.registry.dataset_record import DatasetRecord


class DatasetAvailability:
    """Provide resolvable availability for registered dataset content."""

    def __init__(
        self,
        access: DatasetAccess,
        content_store: DatasetContentStore,
    ) -> None:
        self._access = access
        self._content_store = content_store
        self._availability_registry = DatasetAvailabilityRegistry()
        self._service = DatasetAvailabilityService(
            access, content_store, self._availability_registry
        )

    def publish(
        self, dataset_id: str, version: str, content: list[MarketData]
    ) -> Optional[DatasetContentReference]:
        """Associate content with a registered dataset and expose a resolvable reference."""
        try:
            available = self._service.publish(dataset_id, version, content)
        except ValueError:
            return None
        return available.content_reference

    def resolve(
        self, reference: DatasetContentReference
    ) -> Optional[tuple[DatasetRecord, tuple[MarketData, ...]]]:
        """Resolve the dataset record and its associated content."""
        record = self._access.get(reference.dataset_id, reference.version)
        if record is None:
            return None

        content = self._service.resolve(reference)
        if content is None:
            return None

        return record, content
