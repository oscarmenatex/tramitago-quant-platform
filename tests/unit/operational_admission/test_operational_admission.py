from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_admission import (
    AdmissionDecision,
    OperationalAdmission,
    OperationalAdmissionBoundary,
    OperationalAdmissionDomainError,
    OperationalAdmissionObservation,
    recognize_admission,
)
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def _submission() -> OperationalSubmission:
    instrument = InstrumentReference("FIGI", "ADMISSION-TEST")
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
    return OperationalSubmission(OperationalRequest(OperationalIntent(transition)))


class StaticBoundary:
    def __init__(self, observation: OperationalAdmissionObservation) -> None:
        self.observation = observation
        self.observed: list[OperationalSubmission] = []

    def observe(
        self, submission: OperationalSubmission
    ) -> OperationalAdmissionObservation:
        self.observed.append(submission)
        return self.observation


@pytest.mark.parametrize(
    ("observation", "decision"),
    [
        (OperationalAdmissionObservation(admitted=True), AdmissionDecision.ADMITTED),
        (OperationalAdmissionObservation(rejected=True), AdmissionDecision.REJECTED),
    ],
)
def test_recognizes_only_authorized_decisions_and_preserves_submission(
    observation: OperationalAdmissionObservation,
    decision: AdmissionDecision,
) -> None:
    submission = _submission()
    boundary = StaticBoundary(observation)

    admission = recognize_admission(submission, boundary)

    assert boundary.observed == [submission]
    assert boundary.observed[0] is submission
    assert isinstance(admission, OperationalAdmission)
    assert admission.submission is submission
    assert admission.decision is decision


@pytest.mark.parametrize(
    "observation",
    [
        OperationalAdmissionObservation(),
        OperationalAdmissionObservation(admitted=True, rejected=True),
    ],
)
def test_insufficient_or_ambiguous_observation_produces_no_admission(
    observation: OperationalAdmissionObservation,
) -> None:
    admission: OperationalAdmission | None = None

    with pytest.raises(OperationalAdmissionDomainError):
        admission = recognize_admission(_submission(), StaticBoundary(observation))

    assert admission is None


def test_boundary_failure_is_translated_to_the_single_public_error() -> None:
    class ProviderFailure(Exception):
        pass

    class FailingBoundary:
        def observe(
            self, submission: OperationalSubmission
        ) -> OperationalAdmissionObservation:
            raise ProviderFailure("private failure")

    with pytest.raises(OperationalAdmissionDomainError) as captured:
        recognize_admission(_submission(), FailingBoundary())

    assert isinstance(captured.value.__cause__, ProviderFailure)


def test_boundary_must_provide_an_observation_not_a_decision() -> None:
    class DecisionOwningBoundary:
        def observe(self, submission: OperationalSubmission) -> AdmissionDecision:
            return AdmissionDecision.ADMITTED

    boundary: OperationalAdmissionBoundary = DecisionOwningBoundary()  # type: ignore[assignment]

    with pytest.raises(OperationalAdmissionDomainError):
        recognize_admission(_submission(), boundary)


def test_distinct_boundaries_are_contractually_substitutable() -> None:
    class ComputedBoundary:
        def observe(
            self, submission: OperationalSubmission
        ) -> OperationalAdmissionObservation:
            return OperationalAdmissionObservation(admitted=bool(submission))

    submission = _submission()
    static = recognize_admission(
        submission, StaticBoundary(OperationalAdmissionObservation(admitted=True))
    )
    computed = recognize_admission(submission, ComputedBoundary())

    assert static == computed


def test_admission_is_observably_immutable_and_contractually_minimal() -> None:
    admission = recognize_admission(
        _submission(), StaticBoundary(OperationalAdmissionObservation(admitted=True))
    )

    assert [field.name for field in fields(OperationalAdmission)] == [
        "submission",
        "decision",
    ]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        admission.decision = AdmissionDecision.REJECTED  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        admission.submission = _submission()  # type: ignore[misc]


def test_admission_decision_has_no_third_state() -> None:
    assert tuple(AdmissionDecision) == (
        AdmissionDecision.ADMITTED,
        AdmissionDecision.REJECTED,
    )
    with pytest.raises(ValueError):
        AdmissionDecision("PENDING")


@pytest.mark.parametrize("invalid", [None, object(), "submission"])
def test_recognition_rejects_invalid_submissions(invalid: object) -> None:
    with pytest.raises(OperationalAdmissionDomainError):
        recognize_admission(  # type: ignore[arg-type]
            invalid, StaticBoundary(OperationalAdmissionObservation(admitted=True))
        )
