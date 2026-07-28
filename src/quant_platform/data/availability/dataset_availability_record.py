"""Immutable contracts for published dataset availability."""

from dataclasses import dataclass
from datetime import datetime

from quant_platform.data.availability.dataset_content_reference import (
    DatasetContentReference,
)


@dataclass(frozen=True)
class DatasetCoverage:
    """Descriptive coverage of available content, without provider details."""

    symbols: tuple[str, ...]
    start: datetime | None
    end: datetime | None
    record_count: int


@dataclass(frozen=True)
class DatasetAvailabilityRecord:
    """Internal traceability record for one AVAILABLE dataset version."""

    dataset_id: str
    version: str
    content_reference: DatasetContentReference
    quality_report_id: str
    status: str
    created_at: datetime
    coverage: DatasetCoverage


@dataclass(frozen=True)
class AvailableDataset:
    """Stable read-only contract consumed by internal research clients."""

    dataset_id: str
    version: str
    content_reference: DatasetContentReference
    quality_reference: str
    coverage: DatasetCoverage
