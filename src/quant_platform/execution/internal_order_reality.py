"""Qualification of complete internal order lifecycle reality."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_submission import OperationalSubmission

from .domain import ExecutionDomainError
from .order_reality import OrderLifecycleMeaning, OrderRealityReferenceTime
from .order_terminal_state import ExternalOrderTerminalState, OrderTerminalState


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


def _require_meanings(value: object) -> frozenset[OrderLifecycleMeaning]:
    if not isinstance(value, frozenset):
        raise ExecutionDomainError(
            "Internal order reality meanings must be a frozenset."
        )
    if not all(isinstance(item, OrderLifecycleMeaning) for item in value):
        raise ExecutionDomainError(
            "Internal order reality meanings must contain only "
            "OrderLifecycleMeaning values."
        )
    return value


def _fact_meaning(
    fact: OperationalAdmission | ExternalOrderTerminalState,
) -> OrderLifecycleMeaning:
    if isinstance(fact, OperationalAdmission):
        return (
            OrderLifecycleMeaning.ADMITTED
            if fact.decision is AdmissionDecision.ADMITTED
            else OrderLifecycleMeaning.REJECTED
        )
    return (
        OrderLifecycleMeaning.CANCELLED
        if fact.state is OrderTerminalState.CANCELLED
        else OrderLifecycleMeaning.EXPIRED
    )


@dataclass(frozen=True, slots=True)
class InternalOrderRealityAuthority:
    """Opaque internal authority asserting complete order reality evidence."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ExecutionDomainError(
                "Internal order reality authority must be a non-empty string."
            )


@dataclass(frozen=True, slots=True)
class SupportingInternalOrderRealityEvidence:
    """One complete internal lifecycle assertion for a submitted order."""

    authority: InternalOrderRealityAuthority
    reference_time: OrderRealityReferenceTime
    observed_at_utc: datetime
    submission: OperationalSubmission
    meanings: frozenset[OrderLifecycleMeaning]
    supporting_facts: tuple[OperationalAdmission | ExternalOrderTerminalState, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.authority, InternalOrderRealityAuthority):
            raise ExecutionDomainError(
                "Internal order evidence requires an InternalOrderRealityAuthority."
            )
        if not isinstance(self.reference_time, OrderRealityReferenceTime):
            raise ExecutionDomainError(
                "Internal order evidence requires an OrderRealityReferenceTime."
            )
        _require_utc_datetime(
            self.observed_at_utc, "Internal order evidence observed_at_utc"
        )
        if not isinstance(self.submission, OperationalSubmission):
            raise ExecutionDomainError(
                "Internal order evidence requires one public OperationalSubmission."
            )
        meanings = _require_meanings(self.meanings)
        if not isinstance(self.supporting_facts, tuple):
            raise ExecutionDomainError(
                "Internal order evidence supporting_facts must be a tuple."
            )

        supported: set[OrderLifecycleMeaning] = set()
        for fact in self.supporting_facts:
            if not isinstance(fact, (OperationalAdmission, ExternalOrderTerminalState)):
                raise ExecutionDomainError(
                    "Internal order evidence accepts only OperationalAdmission or "
                    "ExternalOrderTerminalState supporting facts."
                )
            if fact.submission is not self.submission:
                raise ExecutionDomainError(
                    "Every supporting fact must preserve the evidence submission "
                    "instance."
                )
            meaning = _fact_meaning(fact)
            if meaning not in meanings:
                raise ExecutionDomainError(
                    "Every supporting fact must support a declared meaning."
                )
            supported.add(meaning)

        if supported != set(meanings):
            raise ExecutionDomainError(
                "Every declared internal order meaning requires supporting provenance."
            )


@dataclass(frozen=True, slots=True, init=False)
class InternalOrderReality:
    """Qualified complete internal order reality for exactly one scope."""

    reference_time: OrderRealityReferenceTime
    submission: OperationalSubmission
    meanings: frozenset[OrderLifecycleMeaning]
    supporting_evidence: tuple[SupportingInternalOrderRealityEvidence, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "InternalOrderReality must be produced by qualify_internal_order_reality."
        )

    @classmethod
    def _create(
        cls,
        evidence: tuple[SupportingInternalOrderRealityEvidence, ...],
    ) -> "InternalOrderReality":
        reality = object.__new__(cls)
        first = evidence[0]
        object.__setattr__(reality, "reference_time", first.reference_time)
        object.__setattr__(reality, "submission", first.submission)
        object.__setattr__(reality, "meanings", first.meanings)
        object.__setattr__(reality, "supporting_evidence", evidence)
        return reality


def qualify_internal_order_reality(
    evidence: Iterable[SupportingInternalOrderRealityEvidence],
) -> InternalOrderReality:
    """Qualify compatible complete evidence as one internal order reality."""
    try:
        supporting_evidence = tuple(evidence)
    except TypeError as error:
        raise ExecutionDomainError(
            "Internal order reality qualification requires iterable evidence."
        ) from error
    if not supporting_evidence:
        raise ExecutionDomainError(
            "Internal order reality qualification requires at least one evidence."
        )
    if not all(
        isinstance(item, SupportingInternalOrderRealityEvidence)
        for item in supporting_evidence
    ):
        raise ExecutionDomainError(
            "Internal order reality qualification requires only "
            "SupportingInternalOrderRealityEvidence values."
        )

    first = supporting_evidence[0]
    for item in supporting_evidence[1:]:
        if item.submission is not first.submission:
            raise ExecutionDomainError(
                "All internal order evidence must preserve the same submission "
                "instance."
            )
        if item.reference_time != first.reference_time:
            raise ExecutionDomainError(
                "All internal order evidence must have the same reference time."
            )
        if item.meanings != first.meanings:
            raise ExecutionDomainError(
                "Complete internal order evidence must assert identical meanings."
            )

    return InternalOrderReality._create(supporting_evidence)


__all__ = [
    "InternalOrderReality",
    "InternalOrderRealityAuthority",
    "SupportingInternalOrderRealityEvidence",
    "qualify_internal_order_reality",
]
