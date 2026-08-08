from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import (
    OperationalPresentationBoundary,
    OperationalSubmission,
    OperationalSubmissionDomainError,
    submit,
)
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def _request() -> OperationalRequest:
    instrument = InstrumentReference("FIGI", "SUBMIT-ME")
    currency = CurrencyReference("USD")
    current = PortfolioState(
        (PortfolioPosition(instrument, Decimal("1")),),
        (MonetaryBalance(currency, Decimal("100")),),
    )
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal("3")),),
        (MonetaryBalance(currency, Decimal("80")),),
    )
    transition = PortfolioTransition(
        current,
        target,
        (PortfolioPositionTransition(instrument, Decimal("2")),),
        (PortfolioMonetaryTransition(currency, Decimal("-20")),),
    )
    return OperationalRequest(OperationalIntent(transition))


class RecordingBoundary:
    def __init__(self) -> None:
        self.presented: list[OperationalRequest] = []

    def present(self, operational_request: OperationalRequest) -> None:
        self.presented.append(operational_request)


class CountingBoundary:
    def __init__(self) -> None:
        self.count = 0

    def present(self, operational_request: OperationalRequest) -> None:
        self.count += 1


def test_submit_presents_request_and_produces_exactly_one_traceable_fact() -> None:
    request = _request()
    boundary = RecordingBoundary()

    submission = submit(request, boundary)

    assert boundary.presented == [request]
    assert boundary.presented[0] is request
    assert isinstance(submission, OperationalSubmission)
    assert submission.operational_request is request
    assert submission.operational_request.operations is request.operations


def test_presentation_failure_is_translated_and_produces_no_submission() -> None:
    request = _request()

    class FailingBoundary:
        def present(self, operational_request: OperationalRequest) -> None:
            raise OSError("private infrastructure failure")

    submission: OperationalSubmission | None = None
    with pytest.raises(OperationalSubmissionDomainError) as captured:
        submission = submit(request, FailingBoundary())

    assert submission is None
    assert isinstance(captured.value.__cause__, OSError)


def test_boundary_is_replaceable_and_needs_no_external_result() -> None:
    request = _request()
    recording = RecordingBoundary()
    counting = CountingBoundary()

    first = submit(request, recording)
    second = submit(request, counting)

    assert first.operational_request is request
    assert second.operational_request is request
    assert recording.presented == [request]
    assert counting.count == 1


def test_submission_is_observably_immutable_and_has_only_request_field() -> None:
    request = _request()
    submission = submit(request, RecordingBoundary())

    assert [field.name for field in fields(OperationalSubmission)] == [
        "operational_request"
    ]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        submission.operational_request = _request()  # type: ignore[misc]


@pytest.mark.parametrize("invalid", [None, object(), "request"])
def test_submit_rejects_invalid_requests(invalid: object) -> None:
    boundary: OperationalPresentationBoundary = RecordingBoundary()

    with pytest.raises(OperationalSubmissionDomainError):
        submit(invalid, boundary)  # type: ignore[arg-type]
