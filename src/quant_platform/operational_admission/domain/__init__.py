"""Domain contracts for admission recognition within Execution."""

from .exceptions import OperationalAdmissionDomainError
from .operational_admission import (
    AdmissionDecision,
    OperationalAdmission,
    OperationalAdmissionBoundary,
    OperationalAdmissionObservation,
    recognize_admission,
)

__all__ = [
    "OperationalAdmission",
    "AdmissionDecision",
    "OperationalAdmissionObservation",
    "OperationalAdmissionBoundary",
    "recognize_admission",
    "OperationalAdmissionDomainError",
]
