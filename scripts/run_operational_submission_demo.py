#!/usr/bin/env python3
"""Deterministic demonstration of Execution External Presentation."""

from decimal import Decimal

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.execution import prepare_operational_request
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import (
    OperationalSubmission,
    OperationalSubmissionDomainError,
    submit,
)
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.risk import (
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    publication_id = "submission-demo"


class ControlledPresentationBoundary:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.presented_request: OperationalRequest | None = None

    def present(self, operational_request: OperationalRequest) -> None:
        if self.fail:
            raise OSError("controlled presentation failure")
        self.presented_request = operational_request


def _request(quantity: str, limit: str) -> OperationalRequest:
    instrument = InstrumentReference("FIGI", "SUBMIT-DEMO")
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", PublicPublication())
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    constraint = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal(limit), "SHARES"
    )
    result = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-demo-v1",
        (constraint,),
    )
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal(quantity)),),
        current_portfolio_state=PortfolioState(),
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-demo-v1",
    )
    return prepare_operational_request(target)


def main() -> None:
    request = _request("2", "2")
    boundary = ControlledPresentationBoundary()
    submission = submit(request, boundary)
    assert isinstance(submission, OperationalSubmission)
    assert boundary.presented_request is request
    assert submission.operational_request is request

    blocked_boundary = ControlledPresentationBoundary()
    try:
        submit(_request("3", "2"), blocked_boundary)
    except OperationalSubmissionDomainError:
        pass
    else:
        raise AssertionError("Non-presentable request crossed the boundary")
    assert blocked_boundary.presented_request is None

    failed_submission: OperationalSubmission | None = None
    try:
        failed_submission = submit(request, ControlledPresentationBoundary(fail=True))
    except OperationalSubmissionDomainError:
        pass
    else:
        raise AssertionError("Boundary failure produced a submission")
    assert failed_submission is None

    print("unit request preserved:", submission.operational_request is request)
    print("MAX_EXECUTION_SIZE compatible: yes")
    print("non-presentable request stopped before boundary: yes")
    print("boundary failure produced submission: no")
    print("Execution External Presentation demo passed.")


if __name__ == "__main__":
    main()
