"""Recognition of externally evidenced order terminal states."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from quant_platform.operational_submission import OperationalSubmission

from .domain.exceptions import ExecutionDomainError


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


class OrderTerminalState(str, Enum):
    """The exhaustive external order terminal states authorized by IT-034-006."""

    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class ExternalOrderAuthority:
    """Opaque authority that supplied order terminal evidence."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ExecutionDomainError(
                "External order authority must be a non-empty string."
            )


@dataclass(frozen=True, slots=True)
class OrderTerminalReferenceTime:
    """Instant at which the external terminal determination applies."""

    value: datetime

    def __post_init__(self) -> None:
        _require_aware_datetime(self.value, "Order terminal reference time")


@dataclass(frozen=True, slots=True)
class SupportingOrderTerminalEvidence:
    """Normalized external evidence about one submitted order lifecycle."""

    authority: ExternalOrderAuthority
    reference_time: OrderTerminalReferenceTime
    observed_at_utc: datetime
    submission: OperationalSubmission
    cancelled: bool
    expired: bool

    def __post_init__(self) -> None:
        if not isinstance(self.authority, ExternalOrderAuthority):
            raise ExecutionDomainError(
                "Order terminal evidence requires an ExternalOrderAuthority."
            )
        if not isinstance(self.reference_time, OrderTerminalReferenceTime):
            raise ExecutionDomainError(
                "Order terminal evidence requires an OrderTerminalReferenceTime."
            )
        offset = _require_aware_datetime(
            self.observed_at_utc, "Order terminal evidence observed_at_utc"
        )
        if offset != timedelta(0):
            raise ExecutionDomainError(
                "Order terminal evidence observed_at_utc must have exactly UTC offset."
            )
        if not isinstance(self.submission, OperationalSubmission):
            raise ExecutionDomainError(
                "Order terminal evidence requires one public OperationalSubmission."
            )
        if type(self.cancelled) is not bool or type(self.expired) is not bool:
            raise ExecutionDomainError(
                "Order terminal evidence flags must be exact boolean values."
            )


@dataclass(frozen=True, slots=True, init=False)
class ExternalOrderTerminalState:
    """Immutable terminal fact produced only by domain recognition."""

    submission: OperationalSubmission
    state: OrderTerminalState
    supporting_evidence: SupportingOrderTerminalEvidence

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExternalOrderTerminalState must be produced by "
            "recognize_order_terminal_state."
        )

    @classmethod
    def _create(
        cls,
        submission: OperationalSubmission,
        state: OrderTerminalState,
        evidence: SupportingOrderTerminalEvidence,
    ) -> "ExternalOrderTerminalState":
        terminal = object.__new__(cls)
        object.__setattr__(terminal, "submission", submission)
        object.__setattr__(terminal, "state", state)
        object.__setattr__(terminal, "supporting_evidence", evidence)
        return terminal


def recognize_order_terminal_state(
    submission: OperationalSubmission,
    evidence: SupportingOrderTerminalEvidence,
) -> ExternalOrderTerminalState:
    """Recognize one unambiguous CANCELLED or EXPIRED external fact."""
    if not isinstance(submission, OperationalSubmission):
        raise ExecutionDomainError(
            "Order terminal recognition requires one public OperationalSubmission."
        )
    if not isinstance(evidence, SupportingOrderTerminalEvidence):
        raise ExecutionDomainError(
            "Order terminal recognition requires SupportingOrderTerminalEvidence."
        )
    if evidence.submission is not submission:
        raise ExecutionDomainError(
            "Order terminal evidence must reference the exact input submission."
        )
    if evidence.cancelled == evidence.expired:
        detail = "contradictory" if evidence.cancelled else "insufficient"
        raise ExecutionDomainError(f"Order terminal evidence is {detail}.")

    state = (
        OrderTerminalState.CANCELLED
        if evidence.cancelled
        else OrderTerminalState.EXPIRED
    )
    return ExternalOrderTerminalState._create(submission, state, evidence)


__all__ = [
    "ExternalOrderAuthority",
    "ExternalOrderTerminalState",
    "OrderTerminalReferenceTime",
    "OrderTerminalState",
    "SupportingOrderTerminalEvidence",
    "recognize_order_terminal_state",
]
