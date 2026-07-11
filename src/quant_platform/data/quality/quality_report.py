"""Data quality evaluation report.

Responsibility:
    Represent the explainable result of a MarketData quality check.

Inputs:
    Dataset identifier, record counters, validation errors, and final status.

Outputs:
    An immutable QualityReport value object.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QualityReport:
    """Explainable quality evaluation result."""

    dataset_id: str
    total_records: int
    missing_records: int
    duplicate_records: int
    validation_errors: list[str] = field(default_factory=list)
    status: str = "PASS"
