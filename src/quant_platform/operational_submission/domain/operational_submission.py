"""Submission of one operational request through a replaceable boundary."""

from dataclasses import dataclass
from typing import Protocol

from quant_platform.operational_request import OperationalRequest

from .exceptions import OperationalSubmissionDomainError


_QUANTITY_UNITS = frozenset({"SHARE", "SHARES", "UNIT", "UNITS", "QUANTITY"})


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


def _ensure_presentable(operational_request: OperationalRequest) -> None:
    operations = operational_request.operations
    if not operations:
        raise OperationalSubmissionDomainError(
            "An empty OperationalRequest has no external activity to present."
        )
    if len(operations) != 1:
        raise OperationalSubmissionDomainError(
            "IT-036-001 permits exactly one InvestmentOperation per presentation."
        )

    operation = operations[0]
    target = operational_request.operational_intent.target_portfolio_state
    contributors = target.contributing_risk_evaluation_results
    if not contributors:
        raise OperationalSubmissionDomainError(
            "OperationalRequest requires accessible contributing Risk provenance."
        )

    for result in contributors:
        proposition = result.decision_proposal.economic_proposition
        if proposition.instrument != operation.instrument:
            continue
        for constraint in result.constraints:
            if constraint.kind.value != "MAX_EXECUTION_SIZE":
                continue
            if constraint.unit.strip().upper() not in _QUANTITY_UNITS:
                raise OperationalSubmissionDomainError(
                    "MAX_EXECUTION_SIZE unit is not interpretable as operation quantity."
                )
            if operation.quantity > constraint.limit:
                raise OperationalSubmissionDomainError(
                    "InvestmentOperation exceeds MAX_EXECUTION_SIZE."
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

    _ensure_presentable(operational_request)

    try:
        presentation_boundary.present(operational_request)
    except Exception as error:
        raise OperationalSubmissionDomainError(
            "The operational request presentation did not complete."
        ) from error

    return OperationalSubmission(operational_request)
