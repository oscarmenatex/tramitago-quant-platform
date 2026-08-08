"""Submission of one operational request through a replaceable boundary."""

from dataclasses import dataclass
from typing import Protocol

from quant_platform.operational_request import OperationalRequest

from .exceptions import OperationalSubmissionDomainError


class OperationalPresentationBoundary(Protocol):
    """Replaceable technical boundary that presents operational requests."""

    def present(self, operational_request: OperationalRequest) -> None:
        """Complete normally only after the request has been presented."""
        ...


@dataclass(frozen=True, slots=True)
class OperationalSubmission:
    """Immutable fact that one operational request was presented."""

    operational_request: OperationalRequest

    def __post_init__(self) -> None:
        if not isinstance(self.operational_request, OperationalRequest):
            raise OperationalSubmissionDomainError(
                "OperationalSubmission requires one public OperationalRequest."
            )


def submit(
    operational_request: OperationalRequest,
    presentation_boundary: OperationalPresentationBoundary,
) -> OperationalSubmission:
    """Present a valid request and publish the resulting contractual fact."""
    if not isinstance(operational_request, OperationalRequest):
        raise OperationalSubmissionDomainError(
            "submit requires one public OperationalRequest."
        )

    try:
        presentation_boundary.present(operational_request)
    except Exception as error:
        raise OperationalSubmissionDomainError(
            "The operational request presentation did not complete."
        ) from error

    return OperationalSubmission(operational_request)
