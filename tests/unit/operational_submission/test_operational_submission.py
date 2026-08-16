from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.execution import OperationDirection, prepare_operational_request
from quant_platform.operational_admission import OperationalAdmission
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import (
    OperationalPresentationBoundary,
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
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def _risk(
    instrument: InstrumentReference,
    constraint: RiskConstraint | None = None,
) -> RiskEvaluationResult:
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(
        resolution, "publication", PublicPublication(instrument.identification_value)
    )
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    return RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED
        if constraint
        else RiskEvaluationOutcome.ACCEPTED,
        "risk-v1",
        (constraint,) if constraint else (),
    )


def _request(
    changes: tuple[tuple[str, str, str], ...] = (("SUBMIT-ME", "1", "3"),),
    constraint: RiskConstraint | None = None,
) -> OperationalRequest:
    instruments = tuple(InstrumentReference("FIGI", item[0]) for item in changes)
    current = PortfolioState(
        tuple(
            PortfolioPosition(instrument, Decimal(item[1]))
            for instrument, item in zip(instruments, changes, strict=True)
            if Decimal(item[1])
        )
    )
    results = tuple(
        _risk(instrument, constraint if index == 0 else None)
        for index, instrument in enumerate(instruments)
    )
    target = PortfolioState(
        tuple(
            PortfolioPosition(instrument, Decimal(item[2]))
            for instrument, item in zip(instruments, changes, strict=True)
            if Decimal(item[2])
        ),
        current_portfolio_state=current,
        considered_risk_evaluation_results=results,
        contributing_risk_evaluation_results=results,
        determination_basis_reference="portfolio-v1",
    )
    return prepare_operational_request(target)


class RecordingBoundary:
    def __init__(self) -> None:
        self.presented: list[OperationalRequest] = []

    def present(self, operational_request: OperationalRequest) -> None:
        self.presented.append(operational_request)


@pytest.mark.parametrize(
    ("changes", "direction"),
    [
        ((("BUY", "1", "3"),), OperationDirection.BUY),
        ((("SELL", "3", "1"),), OperationDirection.SELL),
    ],
)
def test_unit_request_is_presented_and_preserved(changes, direction) -> None:
    request = _request(changes)
    boundary = RecordingBoundary()
    submission = submit(request, boundary)
    assert request.operations[0].direction is direction
    assert boundary.presented == [request]
    assert boundary.presented[0] is request
    assert submission.operational_request is request
    assert submission.operational_request.operations is request.operations


def test_empty_request_fails_before_boundary() -> None:
    request = _request((("NO-OP", "2", "2"),))
    boundary = RecordingBoundary()
    with pytest.raises(OperationalSubmissionDomainError, match="empty"):
        submit(request, boundary)
    assert boundary.presented == []


def test_multi_operation_request_fails_without_decomposition() -> None:
    request = _request((("A", "0", "2"), ("B", "3", "1")))
    boundary = RecordingBoundary()
    with pytest.raises(OperationalSubmissionDomainError, match="exactly one"):
        submit(request, boundary)
    assert boundary.presented == []
    assert len(request.operations) == 2


def test_max_execution_size_is_enforced_before_boundary() -> None:
    allowed = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("2"), "SHARES"
    )
    blocked = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("1"), "SHARES"
    )
    allowed_boundary = RecordingBoundary()
    blocked_boundary = RecordingBoundary()
    assert submit(_request(constraint=allowed), allowed_boundary)
    with pytest.raises(OperationalSubmissionDomainError, match="exceeds"):
        submit(_request(constraint=blocked), blocked_boundary)
    assert len(allowed_boundary.presented) == 1
    assert blocked_boundary.presented == []


def test_uninterpretable_execution_limit_fails_before_boundary() -> None:
    constraint = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("10"), "USD"
    )
    boundary = RecordingBoundary()
    with pytest.raises(OperationalSubmissionDomainError, match="not interpretable"):
        submit(_request(constraint=constraint), boundary)
    assert boundary.presented == []


def test_composition_constraint_is_not_reinterpreted_at_presentation() -> None:
    constraint = RiskConstraint(RiskConstraintKind.MAX_SIZE, Decimal("1"), "SHARES")
    boundary = RecordingBoundary()
    submission = submit(_request(constraint=constraint), boundary)
    assert submission.operational_request is boundary.presented[0]


def test_boundary_failure_produces_no_submission() -> None:
    class FailingBoundary:
        def present(self, operational_request: OperationalRequest) -> None:
            raise OSError("private infrastructure failure")

    submission: OperationalSubmission | None = None
    with pytest.raises(OperationalSubmissionDomainError) as captured:
        submission = submit(_request(), FailingBoundary())
    assert submission is None
    assert isinstance(captured.value.__cause__, OSError)


def test_boundaries_are_replaceable_and_need_no_external_result() -> None:
    class CountingBoundary:
        def __init__(self) -> None:
            self.count = 0

        def present(self, operational_request: OperationalRequest) -> None:
            self.count += 1

    request = _request()
    recording = RecordingBoundary()
    counting = CountingBoundary()
    assert submit(request, recording).operational_request is request
    assert submit(request, counting).operational_request is request
    assert recording.presented == [request]
    assert counting.count == 1


def test_submission_is_immutable_minimal_and_not_downstream_fact() -> None:
    request = _request()
    submission = submit(request, RecordingBoundary())
    assert [field.name for field in fields(OperationalSubmission)] == [
        "operational_request"
    ]
    assert not isinstance(submission, OperationalAdmission)
    assert not isinstance(submission, OperationalMaterialization)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        submission.operational_request = _request()  # type: ignore[misc]


@pytest.mark.parametrize("invalid", [None, object(), "request"])
def test_submit_rejects_invalid_requests_before_boundary(invalid: object) -> None:
    boundary: OperationalPresentationBoundary = RecordingBoundary()
    with pytest.raises(OperationalSubmissionDomainError):
        submit(invalid, boundary)  # type: ignore[arg-type]
    assert boundary.presented == []  # type: ignore[attr-defined]
