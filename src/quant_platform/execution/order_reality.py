"""Qualification of complete external order lifecycle reality."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from quant_platform.operational_submission import OperationalSubmission

from .domain import ExecutionDomainError


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


class OrderLifecycleMeaning(str, Enum):
    """The exhaustive lifecycle meanings reconciliable by IT-034-007."""

    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class ExternalOrderRealityAuthority:
    """Opaque authority asserting a complete external order reality."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ExecutionDomainError(
                "External order reality authority must be a non-empty string."
            )


@dataclass(frozen=True, slots=True)
class OrderRealityReferenceTime:
    """Unambiguous instant to which an external order reality refers."""

    value: datetime

    def __post_init__(self) -> None:
        _require_aware_datetime(self.value, "Order reality reference time")


def _require_meanings(value: object) -> frozenset[OrderLifecycleMeaning]:
    if not isinstance(value, frozenset):
        raise ExecutionDomainError("Order reality meanings must be a frozenset.")
    if not all(isinstance(item, OrderLifecycleMeaning) for item in value):
        raise ExecutionDomainError(
            "Order reality meanings must contain only OrderLifecycleMeaning values."
        )
    return value


@dataclass(frozen=True, slots=True)
class SupportingExternalOrderRealityEvidence:
    """One complete external lifecycle assertion for a submitted order."""

    authority: ExternalOrderRealityAuthority
    reference_time: OrderRealityReferenceTime
    observed_at_utc: datetime
    submission: OperationalSubmission
    meanings: frozenset[OrderLifecycleMeaning]

    def __post_init__(self) -> None:
        if not isinstance(self.authority, ExternalOrderRealityAuthority):
            raise ExecutionDomainError(
                "Order reality evidence requires an ExternalOrderRealityAuthority."
            )
        if not isinstance(self.reference_time, OrderRealityReferenceTime):
            raise ExecutionDomainError(
                "Order reality evidence requires an OrderRealityReferenceTime."
            )
        offset = _require_aware_datetime(
            self.observed_at_utc, "Order reality evidence observed_at_utc"
        )
        if offset != timedelta(0):
            raise ExecutionDomainError(
                "Order reality evidence observed_at_utc must have exactly UTC offset."
            )
        if not isinstance(self.submission, OperationalSubmission):
            raise ExecutionDomainError(
                "Order reality evidence requires one public OperationalSubmission."
            )
        _require_meanings(self.meanings)


@dataclass(frozen=True, slots=True, init=False)
class ExternalOrderReality:
    """Qualified complete external order reality for exactly one scope."""

    authority: ExternalOrderRealityAuthority
    reference_time: OrderRealityReferenceTime
    submission: OperationalSubmission
    meanings: frozenset[OrderLifecycleMeaning]
    supporting_evidence: tuple[SupportingExternalOrderRealityEvidence, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExternalOrderReality must be produced by qualify_external_order_reality."
        )

    @classmethod
    def _create(
        cls,
        evidence: tuple[SupportingExternalOrderRealityEvidence, ...],
    ) -> "ExternalOrderReality":
        reality = object.__new__(cls)
        first = evidence[0]
        object.__setattr__(reality, "authority", first.authority)
        object.__setattr__(reality, "reference_time", first.reference_time)
        object.__setattr__(reality, "submission", first.submission)
        object.__setattr__(reality, "meanings", first.meanings)
        object.__setattr__(reality, "supporting_evidence", evidence)
        return reality


def qualify_external_order_reality(
    evidence: Iterable[SupportingExternalOrderRealityEvidence],
) -> ExternalOrderReality:
    """Qualify compatible complete evidence as one external order reality."""
    try:
        supporting_evidence = tuple(evidence)
    except TypeError as error:
        raise ExecutionDomainError(
            "External order reality qualification requires iterable evidence."
        ) from error
    if not supporting_evidence:
        raise ExecutionDomainError(
            "External order reality qualification requires at least one evidence."
        )
    if not all(
        isinstance(item, SupportingExternalOrderRealityEvidence)
        for item in supporting_evidence
    ):
        raise ExecutionDomainError(
            "External order reality qualification requires only "
            "SupportingExternalOrderRealityEvidence values."
        )

    first = supporting_evidence[0]
    for item in supporting_evidence[1:]:
        if item.authority != first.authority:
            raise ExecutionDomainError(
                "All order reality evidence must have the same authority."
            )
        if item.submission is not first.submission:
            raise ExecutionDomainError(
                "All order reality evidence must preserve the same submission instance."
            )
        if item.reference_time != first.reference_time:
            raise ExecutionDomainError(
                "All order reality evidence must have the same reference time."
            )
        if item.meanings != first.meanings:
            raise ExecutionDomainError(
                "Complete order reality evidence must assert identical meanings."
            )

    return ExternalOrderReality._create(supporting_evidence)


__all__ = [
    "ExternalOrderReality",
    "ExternalOrderRealityAuthority",
    "OrderLifecycleMeaning",
    "OrderRealityReferenceTime",
    "SupportingExternalOrderRealityEvidence",
    "qualify_external_order_reality",
]
