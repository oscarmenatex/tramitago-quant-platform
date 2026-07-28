"""Dataset registration management."""

from datetime import datetime
from quant_platform.data.registry.dataset_record import DatasetRecord
from quant_platform.data.quality.quality_report import QualityReport


class DatasetRegistry:
    """Register and query datasets within the platform lifecycle."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], DatasetRecord] = {}

    def register(
        self,
        dataset_id: str,
        name: str,
        version: str,
        source: str,
        quality_report: QualityReport,
        status: str = "REGISTERED",
    ) -> DatasetRecord:
        """Create and store a dataset record linked to a QualityReport."""
        if not dataset_id or not dataset_id.strip():
            raise ValueError("dataset_id must be provided")

        record = DatasetRecord(
            dataset_id=dataset_id,
            name=name,
            version=version,
            source=source,
            created_at=datetime.now(),
            quality_report_id=quality_report.dataset_id,
            status=status,
        )
        self._records[(dataset_id, version)] = record
        return record

    def get(self, dataset_id: str, version: str) -> DatasetRecord | None:
        """Return a previously registered dataset record for one version."""
        return self._records.get((dataset_id, version))
