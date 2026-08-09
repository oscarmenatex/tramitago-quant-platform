"""Recognition of an initial external determination for one submission."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from quant_platform.operational_submission import OperationalSubmission

from .exceptions import OperationalAdmissionDomainError


class AdmissionDecision(str, Enum):
    """The only admission determinations authorized by IT-037-001."""

    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class OperationalAdmissionObservation:
    """Normalized external evidence, before contractual recognition."""

    admitted: bool = False
    rejected: bool = False

    def __post_init__(self) -> None:
        if type(self.admitted) is not bool or type(self.rejected) is not bool:
            raise OperationalAdmissionDomainError(
                "Operational admission evidence must use boolean observations."
            )


class OperationalAdmissionBoundary(Protocol):
    """Replaceable boundary that supplies normalized external evidence."""

    def observe(
        self, submission: OperationalSubmission
    ) -> OperationalAdmissionObservation:
        """Observe the initial external evidence for one submission."""
        ...


@dataclass(frozen=True, slots=True)
class OperationalAdmission:
    """Immutable recognized admission determination for one submission."""

    submission: OperationalSubmission
    decision: AdmissionDecision

    def __post_init__(self) -> None:
        if not isinstance(self.submission, OperationalSubmission):
            raise OperationalAdmissionDomainError(
                "OperationalAdmission requires one public OperationalSubmission."
            )
        if not isinstance(self.decision, AdmissionDecision):
            raise OperationalAdmissionDomainError(
                "OperationalAdmission decision must be ADMITTED or REJECTED."
            )


def recognize_admission(
    submission: OperationalSubmission,
    boundary: OperationalAdmissionBoundary,
) -> OperationalAdmission:
    """Recognize normalized evidence and publish an admission fact."""
    if not isinstance(submission, OperationalSubmission):
        raise OperationalAdmissionDomainError(
            "recognize_admission requires one public OperationalSubmission."
        )

    try:
        observation = boundary.observe(submission)
    except Exception as error:
        raise OperationalAdmissionDomainError(
            "The initial external determination could not be observed."
        ) from error

    if not isinstance(observation, OperationalAdmissionObservation):
        raise OperationalAdmissionDomainError(
            "The boundary did not provide an OperationalAdmissionObservation."
        )

    if observation.admitted is observation.rejected:
        raise OperationalAdmissionDomainError(
            "The observation does not identify one unambiguous admission decision."
        )

    decision = (
        AdmissionDecision.ADMITTED
        if observation.admitted
        else AdmissionDecision.REJECTED
    )
    return OperationalAdmission(submission=submission, decision=decision)
