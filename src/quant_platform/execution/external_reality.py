"""Qualification of complete execution reality asserted by an external authority."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from quant_platform.core import CurrencyReference

from .domain import ExecutionDomainError, InvestmentOperation


def _require_non_empty_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionDomainError(f"{label} must be a non-empty string.")


def _require_aware_datetime(value: object, label: str) -> timedelta:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ExecutionDomainError(f"{label} must be a timezone-aware datetime.")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as error:
        raise ExecutionDomainError(
            f"{label} must have a determinable UTC offset."
        ) from error
    if offset is None:
        raise ExecutionDomainError(f"{label} must have a determinable UTC offset.")
    return offset


@dataclass(frozen=True, slots=True)
class ExternalExecutionAuthority:
    """The explicit external authority asserting an execution reality."""

    value: str

    def __post_init__(self) -> None:
        _require_non_empty_text(self.value, "External execution authority")


@dataclass(frozen=True, slots=True)
class ExecutionRealityReferenceTime:
    """The unambiguous instant to which an external reality refers."""

    value: datetime

    def __post_init__(self) -> None:
        _require_aware_datetime(self.value, "Execution reality reference time")


@dataclass(frozen=True, slots=True)
class ReportedExecution:
    """One execution reported with an opaque identity by an external authority."""

    external_execution_id: str
    quantity: Decimal
    price: Decimal
    currency: CurrencyReference

    def __post_init__(self) -> None:
        _require_non_empty_text(self.external_execution_id, "External execution ID")
        if (
            not isinstance(self.quantity, Decimal)
            or not self.quantity.is_finite()
            or self.quantity <= 0
        ):
            raise ExecutionDomainError(
                "Reported execution quantity must be an exact, finite, positive "
                "Decimal."
            )
        if not isinstance(self.price, Decimal) or not self.price.is_finite():
            raise ExecutionDomainError(
                "Reported execution price must be an exact, finite Decimal."
            )
        if not isinstance(self.currency, CurrencyReference):
            raise ExecutionDomainError(
                "Reported execution currency must be a public CurrencyReference."
            )


def _execution_facts(
    reported_executions: tuple[ReportedExecution, ...],
) -> dict[str, tuple[Decimal, Decimal, CurrencyReference]]:
    facts: dict[str, tuple[Decimal, Decimal, CurrencyReference]] = {}
    for execution in reported_executions:
        if not isinstance(execution, ReportedExecution):
            raise ExecutionDomainError(
                "Reported executions must contain only ReportedExecution values."
            )
        if execution.external_execution_id in facts:
            raise ExecutionDomainError(
                "An external execution ID may occur only once in a complete snapshot."
            )
        facts[execution.external_execution_id] = (
            execution.quantity,
            execution.price,
            execution.currency,
        )
    return facts


@dataclass(frozen=True, slots=True)
class SupportingExecutionEvidence:
    """One complete externally observed execution assertion for a single scope."""

    authority: ExternalExecutionAuthority
    reference_time: ExecutionRealityReferenceTime
    observed_at_utc: datetime
    operation: InvestmentOperation
    reported_executions: tuple[ReportedExecution, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.authority, ExternalExecutionAuthority):
            raise ExecutionDomainError(
                "Supporting evidence requires an ExternalExecutionAuthority."
            )
        if not isinstance(self.reference_time, ExecutionRealityReferenceTime):
            raise ExecutionDomainError(
                "Supporting evidence requires an ExecutionRealityReferenceTime."
            )
        offset = _require_aware_datetime(
            self.observed_at_utc, "Supporting evidence observed_at_utc"
        )
        if offset != timedelta(0):
            raise ExecutionDomainError(
                "Supporting evidence observed_at_utc must have exactly UTC offset."
            )
        if not isinstance(self.operation, InvestmentOperation):
            raise ExecutionDomainError(
                "Supporting evidence requires a public InvestmentOperation."
            )
        if not isinstance(self.reported_executions, tuple):
            raise ExecutionDomainError(
                "Supporting evidence reported_executions must be a tuple."
            )
        _execution_facts(self.reported_executions)


@dataclass(frozen=True, slots=True, init=False)
class ExternalExecutionReality:
    """A qualified complete external execution reality for exactly one scope."""

    authority: ExternalExecutionAuthority
    reference_time: ExecutionRealityReferenceTime
    operation: InvestmentOperation
    reported_executions: tuple[ReportedExecution, ...]
    supporting_evidence: tuple[SupportingExecutionEvidence, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExternalExecutionReality must be produced by "
            "qualify_external_execution_reality."
        )

    @classmethod
    def _create(
        cls,
        evidence: tuple[SupportingExecutionEvidence, ...],
    ) -> "ExternalExecutionReality":
        reality = object.__new__(cls)
        first = evidence[0]
        object.__setattr__(reality, "authority", first.authority)
        object.__setattr__(reality, "reference_time", first.reference_time)
        object.__setattr__(reality, "operation", first.operation)
        object.__setattr__(
            reality, "reported_executions", first.reported_executions
        )
        object.__setattr__(reality, "supporting_evidence", evidence)
        return reality


def qualify_external_execution_reality(
    evidence: Iterable[SupportingExecutionEvidence],
) -> ExternalExecutionReality:
    """Qualify compatible complete evidence as one external execution reality."""
    try:
        supporting_evidence = tuple(evidence)
    except TypeError as error:
        raise ExecutionDomainError(
            "External execution reality qualification requires iterable evidence."
        ) from error
    if not supporting_evidence:
        raise ExecutionDomainError(
            "External execution reality qualification requires at least one evidence."
        )
    if not all(
        isinstance(item, SupportingExecutionEvidence) for item in supporting_evidence
    ):
        raise ExecutionDomainError(
            "External execution reality qualification requires only "
            "SupportingExecutionEvidence values."
        )

    first = supporting_evidence[0]
    expected_facts = _execution_facts(first.reported_executions)
    for item in supporting_evidence[1:]:
        if item.authority != first.authority:
            raise ExecutionDomainError(
                "All supporting evidence must have the same external authority."
            )
        if item.operation != first.operation:
            raise ExecutionDomainError(
                "All supporting evidence must have the same InvestmentOperation."
            )
        if item.reference_time != first.reference_time:
            raise ExecutionDomainError(
                "All supporting evidence must have the same reference time."
            )
        if _execution_facts(item.reported_executions) != expected_facts:
            raise ExecutionDomainError(
                "Complete supporting evidence snapshots must contain identical "
                "reported execution facts."
            )

    return ExternalExecutionReality._create(supporting_evidence)


__all__ = [
    "ExecutionRealityReferenceTime",
    "ExternalExecutionAuthority",
    "ExternalExecutionReality",
    "ReportedExecution",
    "SupportingExecutionEvidence",
    "qualify_external_execution_reality",
]
