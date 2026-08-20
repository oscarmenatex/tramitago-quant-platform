"""Qualification of complete execution reality recognized internally."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from quant_platform.core import CurrencyReference
from quant_platform.operational_materialization import OperationalMaterialization

from .domain import ExecutionDomainError, InvestmentOperation
from .external_reality import ExecutionRealityReferenceTime


def _require_utc_datetime(value: object, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ExecutionDomainError(f"{label} must be a timezone-aware datetime.")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as error:
        raise ExecutionDomainError(
            f"{label} must have a determinable UTC offset."
        ) from error
    if offset != timedelta(0):
        raise ExecutionDomainError(f"{label} must have exactly UTC offset.")


@dataclass(frozen=True, slots=True)
class InternalExecutionAuthority:
    """An explicit opaque internal source recognized by Execution."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ExecutionDomainError(
                "Internal execution authority must be a non-empty string."
            )


def _materialization_facts(
    operation: InvestmentOperation,
    materializations: tuple[OperationalMaterialization, ...],
) -> dict[str, tuple[Decimal, Decimal, CurrencyReference]]:
    facts: dict[str, tuple[Decimal, Decimal, CurrencyReference]] = {}
    for materialization in materializations:
        if not isinstance(materialization, OperationalMaterialization):
            raise ExecutionDomainError(
                "Materializations must contain only OperationalMaterialization values."
            )
        if materialization.operation != operation:
            raise ExecutionDomainError(
                "Every materialization must correspond to the evidence operation."
            )
        if materialization.occurrence_id in facts:
            raise ExecutionDomainError(
                "An occurrence_id may occur only once in a complete snapshot."
            )
        facts[materialization.occurrence_id] = (
            materialization.quantity,
            materialization.price,
            materialization.currency,
        )
    return facts


@dataclass(frozen=True, slots=True)
class SupportingInternalExecutionEvidence:
    """One complete internal execution assertion for a single scope and cut."""

    authority: InternalExecutionAuthority
    reference_time: ExecutionRealityReferenceTime
    observed_at_utc: datetime
    operation: InvestmentOperation
    materializations: tuple[OperationalMaterialization, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.authority, InternalExecutionAuthority):
            raise ExecutionDomainError(
                "Supporting evidence requires an InternalExecutionAuthority."
            )
        if not isinstance(self.reference_time, ExecutionRealityReferenceTime):
            raise ExecutionDomainError(
                "Supporting evidence requires an ExecutionRealityReferenceTime."
            )
        _require_utc_datetime(
            self.observed_at_utc, "Supporting evidence observed_at_utc"
        )
        if not isinstance(self.operation, InvestmentOperation):
            raise ExecutionDomainError(
                "Supporting evidence requires a public InvestmentOperation."
            )
        if not isinstance(self.materializations, tuple):
            raise ExecutionDomainError(
                "Supporting evidence materializations must be a tuple."
            )
        _materialization_facts(self.operation, self.materializations)


@dataclass(frozen=True, slots=True, init=False)
class InternalExecutionReality:
    """A complete qualified set of executions recognized internally."""

    reference_time: ExecutionRealityReferenceTime
    operation: InvestmentOperation
    materializations: tuple[OperationalMaterialization, ...]
    supporting_evidence: tuple[SupportingInternalExecutionEvidence, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "InternalExecutionReality must be produced by "
            "qualify_internal_execution_reality."
        )

    @classmethod
    def _create(
        cls,
        evidence: tuple[SupportingInternalExecutionEvidence, ...],
    ) -> "InternalExecutionReality":
        reality = object.__new__(cls)
        first = evidence[0]
        object.__setattr__(reality, "reference_time", first.reference_time)
        object.__setattr__(reality, "operation", first.operation)
        object.__setattr__(reality, "materializations", first.materializations)
        object.__setattr__(reality, "supporting_evidence", evidence)
        return reality


def qualify_internal_execution_reality(
    evidence: Iterable[SupportingInternalExecutionEvidence],
) -> InternalExecutionReality:
    """Qualify compatible complete internal evidence as one reality."""
    try:
        supporting_evidence = tuple(evidence)
    except TypeError as error:
        raise ExecutionDomainError(
            "Internal execution reality qualification requires iterable evidence."
        ) from error
    if not supporting_evidence:
        raise ExecutionDomainError(
            "Internal execution reality qualification requires at least one evidence."
        )
    if not all(
        isinstance(item, SupportingInternalExecutionEvidence)
        for item in supporting_evidence
    ):
        raise ExecutionDomainError(
            "Internal execution reality qualification requires only "
            "SupportingInternalExecutionEvidence values."
        )

    first = supporting_evidence[0]
    expected_facts = _materialization_facts(
        first.operation, first.materializations
    )
    for item in supporting_evidence[1:]:
        if item.operation != first.operation:
            raise ExecutionDomainError(
                "All supporting evidence must have the same InvestmentOperation."
            )
        if item.reference_time != first.reference_time:
            raise ExecutionDomainError(
                "All supporting evidence must have the same reference time."
            )
        if _materialization_facts(item.operation, item.materializations) != expected_facts:
            raise ExecutionDomainError(
                "Complete supporting evidence snapshots must contain identical "
                "materialization facts."
            )

    return InternalExecutionReality._create(supporting_evidence)


__all__ = [
    "InternalExecutionAuthority",
    "InternalExecutionReality",
    "SupportingInternalExecutionEvidence",
    "qualify_internal_execution_reality",
]
