"""Recognition and classification of explicitly evidenced external failures."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from quant_platform.operational_admission import OperationalAdmission
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission

from .domain import ExecutionDomainError
from .reconciliation_scope import RequiredReconciliationScope


class ExternalFailureClass(str, Enum):
    """The exhaustive failure classes authorized by IT-034-012."""

    INTERACTION_FAILURE = "INTERACTION_FAILURE"
    EVIDENCE_FAILURE = "EVIDENCE_FAILURE"


class ExternalFailureObligation(str, Enum):
    """The exhaustive externally dependent Execution obligations."""

    OPERATIONAL_PRESENTATION = "OPERATIONAL_PRESENTATION"
    ADMISSION_OBSERVATION = "ADMISSION_OBSERVATION"
    MATERIALIZATION_OBSERVATION = "MATERIALIZATION_OBSERVATION"
    ORDER_TERMINAL_OBSERVATION = "ORDER_TERMINAL_OBSERVATION"
    RECONCILIATION_EVIDENCE_OBSERVATION = (
        "RECONCILIATION_EVIDENCE_OBSERVATION"
    )


@dataclass(frozen=True, slots=True)
class ExternalFailureAuthority:
    """Opaque authority asserting an external failure."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise ExecutionDomainError(
                "External failure authority must be a non-empty string."
            )


def _require_aware_datetime(value: object, label: str) -> timedelta:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ExecutionDomainError(f"{label} must be a timezone-aware datetime.")
    try:
        offset = value.utcoffset()
    except Exception as error:
        raise ExecutionDomainError(
            f"{label} must have a determinable UTC offset."
        ) from error
    if offset is None:
        raise ExecutionDomainError(f"{label} must have a determinable UTC offset.")
    return offset


@dataclass(frozen=True, slots=True)
class ExternalFailureReferenceTime:
    """Instant at which the asserted external failure applies."""

    value: datetime

    def __post_init__(self) -> None:
        _require_aware_datetime(self.value, "External failure reference time")


_CONTEXT_TYPES = {
    ExternalFailureObligation.OPERATIONAL_PRESENTATION: OperationalRequest,
    ExternalFailureObligation.ADMISSION_OBSERVATION: OperationalSubmission,
    ExternalFailureObligation.MATERIALIZATION_OBSERVATION: OperationalAdmission,
    ExternalFailureObligation.ORDER_TERMINAL_OBSERVATION: OperationalSubmission,
    ExternalFailureObligation.RECONCILIATION_EVIDENCE_OBSERVATION: (
        RequiredReconciliationScope
    ),
}


@dataclass(frozen=True, slots=True)
class SupportingExternalFailureEvidence:
    """One complete external assertion of the same failure fact."""

    authority: ExternalFailureAuthority
    obligation: ExternalFailureObligation
    failure_class: ExternalFailureClass
    reference_time: ExternalFailureReferenceTime
    observed_at_utc: datetime
    context: (
        OperationalRequest
        | OperationalSubmission
        | OperationalAdmission
        | RequiredReconciliationScope
    )

    def __post_init__(self) -> None:
        if not isinstance(self.authority, ExternalFailureAuthority):
            raise ExecutionDomainError(
                "External failure evidence requires an ExternalFailureAuthority."
            )
        if not isinstance(self.obligation, ExternalFailureObligation):
            raise ExecutionDomainError(
                "External failure evidence requires an ExternalFailureObligation."
            )
        if not isinstance(self.failure_class, ExternalFailureClass):
            raise ExecutionDomainError(
                "External failure evidence requires an ExternalFailureClass."
            )
        if not isinstance(self.reference_time, ExternalFailureReferenceTime):
            raise ExecutionDomainError(
                "External failure evidence requires an ExternalFailureReferenceTime."
            )
        offset = _require_aware_datetime(
            self.observed_at_utc, "External failure evidence observed_at_utc"
        )
        if offset != timedelta(0):
            raise ExecutionDomainError(
                "External failure evidence observed_at_utc must have exactly UTC "
                "offset zero."
            )
        expected_context = _CONTEXT_TYPES[self.obligation]
        if not isinstance(self.context, expected_context):
            raise ExecutionDomainError(
                "External failure obligation does not match its required context."
            )


@dataclass(frozen=True, slots=True, init=False)
class ExternalFailure:
    """Immutable external failure fact produced only by recognition."""

    obligation: ExternalFailureObligation
    failure_class: ExternalFailureClass
    context: (
        OperationalRequest
        | OperationalSubmission
        | OperationalAdmission
        | RequiredReconciliationScope
    )
    supporting_evidence: tuple[SupportingExternalFailureEvidence, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExternalFailure must be produced by recognize_external_failure."
        )

    @classmethod
    def _create(
        cls,
        evidence: tuple[SupportingExternalFailureEvidence, ...],
    ) -> "ExternalFailure":
        failure = object.__new__(cls)
        first = evidence[0]
        object.__setattr__(failure, "obligation", first.obligation)
        object.__setattr__(failure, "failure_class", first.failure_class)
        object.__setattr__(failure, "context", first.context)
        object.__setattr__(failure, "supporting_evidence", evidence)
        return failure


def recognize_external_failure(
    evidence: Iterable[SupportingExternalFailureEvidence],
) -> ExternalFailure:
    """Recognize compatible complete evidence as one external failure."""
    try:
        supplied = tuple(evidence)
    except (TypeError, RuntimeError) as error:
        raise ExecutionDomainError(
            "External failure recognition requires iterable evidence."
        ) from error
    if not supplied:
        raise ExecutionDomainError(
            "External failure recognition requires at least one evidence."
        )
    if not all(isinstance(item, SupportingExternalFailureEvidence) for item in supplied):
        raise ExecutionDomainError(
            "External failure recognition requires only "
            "SupportingExternalFailureEvidence values."
        )

    unique_by_identity: dict[int, SupportingExternalFailureEvidence] = {}
    for item in supplied:
        unique_by_identity.setdefault(id(item), item)
    supporting_evidence = tuple(unique_by_identity.values())
    first = supporting_evidence[0]
    first_instant = first.reference_time.value.astimezone(timezone.utc)

    for item in supporting_evidence[1:]:
        if item.authority != first.authority:
            raise ExecutionDomainError(
                "All external failure evidence must have the same authority."
            )
        if item.obligation is not first.obligation:
            raise ExecutionDomainError(
                "All external failure evidence must have the same obligation."
            )
        if item.failure_class is not first.failure_class:
            raise ExecutionDomainError(
                "All external failure evidence must have the same failure class."
            )
        if item.context is not first.context:
            raise ExecutionDomainError(
                "All external failure evidence must preserve the same context instance."
            )
        if item.reference_time.value.astimezone(timezone.utc) != first_instant:
            raise ExecutionDomainError(
                "All external failure evidence must have equivalent reference times."
            )

    return ExternalFailure._create(supporting_evidence)


__all__ = [
    "ExternalFailure",
    "ExternalFailureAuthority",
    "ExternalFailureClass",
    "ExternalFailureObligation",
    "ExternalFailureReferenceTime",
    "SupportingExternalFailureEvidence",
    "recognize_external_failure",
]
