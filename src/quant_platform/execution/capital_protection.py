"""Qualification of capital protection for an already-recognized external failure."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from .domain import ExecutionDomainError
from .external_failure import ExternalFailure


def _require_non_empty_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionDomainError(f"{label} must be a non-empty string.")


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


class ExternalFailureCapitalProtectionCondition(str, Enum):
    """The exhaustive capital-protection qualification conditions."""

    PROTECTED = "PROTECTED"
    NOT_DEMONSTRATED = "NOT_DEMONSTRATED"


@dataclass(frozen=True, slots=True)
class CapitalProtectionAuthority:
    """Opaque authority making a positive capital-protection assertion."""

    value: str

    def __post_init__(self) -> None:
        _require_non_empty_text(self.value, "Capital protection authority")


@dataclass(frozen=True, slots=True)
class CapitalProtectionReferenceTime:
    """The exact instant cut governed by a capital-protection qualification."""

    value: datetime

    def __post_init__(self) -> None:
        _require_aware_datetime(self.value, "Capital protection reference time")


@dataclass(frozen=True, slots=True)
class SupportingCapitalProtectionEvidence:
    """One complete positive capital-protection attestation."""

    authority: CapitalProtectionAuthority
    reference_time: CapitalProtectionReferenceTime
    observed_at_utc: datetime
    external_failure: ExternalFailure
    basis_reference: str

    def __post_init__(self) -> None:
        if not isinstance(self.authority, CapitalProtectionAuthority):
            raise ExecutionDomainError(
                "Capital protection evidence requires a CapitalProtectionAuthority."
            )
        if not isinstance(self.reference_time, CapitalProtectionReferenceTime):
            raise ExecutionDomainError(
                "Capital protection evidence requires a CapitalProtectionReferenceTime."
            )
        offset = _require_aware_datetime(
            self.observed_at_utc, "Capital protection evidence observed_at_utc"
        )
        if offset != timedelta(0):
            raise ExecutionDomainError(
                "Capital protection evidence observed_at_utc must have exactly UTC "
                "offset zero."
            )
        if not isinstance(self.external_failure, ExternalFailure):
            raise ExecutionDomainError(
                "Capital protection evidence requires an ExternalFailure."
            )
        _require_non_empty_text(
            self.basis_reference, "Capital protection evidence basis_reference"
        )


@dataclass(frozen=True, slots=True, init=False)
class ExternalFailureCapitalProtectionQualification:
    """Immutable capital-protection qualification for one failure and instant."""

    external_failure: ExternalFailure
    reference_time: CapitalProtectionReferenceTime
    condition: ExternalFailureCapitalProtectionCondition
    supporting_evidence: tuple[SupportingCapitalProtectionEvidence, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ExecutionDomainError(
            "ExternalFailureCapitalProtectionQualification must be produced by "
            "qualify_external_failure_capital_protection."
        )

    @classmethod
    def _create(
        cls,
        external_failure: ExternalFailure,
        reference_time: CapitalProtectionReferenceTime,
        condition: ExternalFailureCapitalProtectionCondition,
        supporting_evidence: tuple[SupportingCapitalProtectionEvidence, ...],
    ) -> "ExternalFailureCapitalProtectionQualification":
        qualification = object.__new__(cls)
        object.__setattr__(qualification, "external_failure", external_failure)
        object.__setattr__(qualification, "reference_time", reference_time)
        object.__setattr__(qualification, "condition", condition)
        object.__setattr__(qualification, "supporting_evidence", supporting_evidence)
        return qualification


def qualify_external_failure_capital_protection(
    external_failure: ExternalFailure,
    reference_time: CapitalProtectionReferenceTime,
    evidence: Iterable[SupportingCapitalProtectionEvidence] = (),
) -> ExternalFailureCapitalProtectionQualification:
    """Qualify applicable positive evidence at an exact failure and instant."""
    if not isinstance(external_failure, ExternalFailure):
        raise ExecutionDomainError(
            "Capital protection qualification requires an ExternalFailure."
        )
    if not isinstance(reference_time, CapitalProtectionReferenceTime):
        raise ExecutionDomainError(
            "Capital protection qualification requires a "
            "CapitalProtectionReferenceTime."
        )
    try:
        supplied = tuple(evidence)
    except (TypeError, RuntimeError) as error:
        raise ExecutionDomainError(
            "Capital protection qualification requires iterable evidence."
        ) from error
    if not all(
        isinstance(item, SupportingCapitalProtectionEvidence) for item in supplied
    ):
        raise ExecutionDomainError(
            "Capital protection qualification requires only "
            "SupportingCapitalProtectionEvidence values."
        )

    requested_instant = reference_time.value.astimezone(timezone.utc)
    applicable: list[SupportingCapitalProtectionEvidence] = []
    seen_instances: set[int] = set()
    for item in supplied:
        identity = id(item)
        if identity in seen_instances:
            continue
        seen_instances.add(identity)
        if item.external_failure is not external_failure:
            continue
        if item.reference_time.value.astimezone(timezone.utc) != requested_instant:
            continue
        applicable.append(item)

    supporting_evidence = tuple(applicable)
    condition = (
        ExternalFailureCapitalProtectionCondition.PROTECTED
        if supporting_evidence
        else ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED
    )
    return ExternalFailureCapitalProtectionQualification._create(
        external_failure, reference_time, condition, supporting_evidence
    )


__all__ = [
    "CapitalProtectionAuthority",
    "CapitalProtectionReferenceTime",
    "ExternalFailureCapitalProtectionCondition",
    "ExternalFailureCapitalProtectionQualification",
    "SupportingCapitalProtectionEvidence",
    "qualify_external_failure_capital_protection",
]
