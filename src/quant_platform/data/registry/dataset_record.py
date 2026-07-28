"""Dataset registry record representation."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DatasetRecord:
    """Administrative representation of a registered dataset."""

    dataset_id: str
    name: str
    version: str
    source: str
    created_at: datetime
    quality_report_id: str
    status: str
