from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderAuthority,
    ExternalOrderTerminalState,
    OrderTerminalReferenceTime,
    OrderTerminalState,
    SupportingOrderTerminalEvidence,
    prepare_operational_request,
    recognize_order_terminal_state,
)
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioState


class IndeterminableTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def _submission(target: PortfolioState) -> OperationalSubmission:
    return OperationalSubmission(prepare_operational_request(target))


def _evidence(
    submission: OperationalSubmission,
    *,
    cancelled: bool = True,
    expired: bool = False,
) -> SupportingOrderTerminalEvidence:
    return SupportingOrderTerminalEvidence(
        authority=ExternalOrderAuthority("broker/account scope:opaque"),
        reference_time=OrderTerminalReferenceTime(
            datetime(2026, 8, 19, 22, 0, tzinfo=timezone(timedelta(hours=-4)))
        ),
        observed_at_utc=datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc),
        submission=submission,
        cancelled=cancelled,
        expired=expired,
    )


@pytest.mark.parametrize(
    ("cancelled", "expired", "state"),
    [
        (True, False, OrderTerminalState.CANCELLED),
        (False, True, OrderTerminalState.EXPIRED),
    ],
)
def test_recognizes_terminal_state_and_preserves_exact_provenance(
    target: PortfolioState,
    cancelled: bool,
    expired: bool,
    state: OrderTerminalState,
) -> None:
    submission = _submission(target)
    evidence = _evidence(submission, cancelled=cancelled, expired=expired)

    terminal = recognize_order_terminal_state(submission, evidence)

    assert terminal.state is state
    assert terminal.submission is submission
    assert terminal.supporting_evidence is evidence
    assert terminal.supporting_evidence.authority is evidence.authority
    assert terminal.supporting_evidence.reference_time is evidence.reference_time
    assert terminal.supporting_evidence.observed_at_utc is evidence.observed_at_utc


@pytest.mark.parametrize("value", ["venue-7", " account / channel ", "opaque:1"])
def test_external_order_authority_accepts_non_empty_opaque_text(value: str) -> None:
    assert ExternalOrderAuthority(value).value == value


@pytest.mark.parametrize("value", ["", "   ", None, 7])
def test_external_order_authority_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalOrderAuthority(value)  # type: ignore[arg-type]


def test_reference_time_requires_a_determinable_offset() -> None:
    with pytest.raises(ExecutionDomainError):
        OrderTerminalReferenceTime(datetime(2026, 8, 20))
    with pytest.raises(ExecutionDomainError):
        OrderTerminalReferenceTime(
            datetime(2026, 8, 20, tzinfo=IndeterminableTimezone())
        )


def test_reference_time_compares_equivalent_instants_across_offsets() -> None:
    utc = OrderTerminalReferenceTime(
        datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc)
    )
    eastern = OrderTerminalReferenceTime(
        datetime(2026, 8, 19, 22, 0, tzinfo=timezone(timedelta(hours=-4)))
    )
    assert utc == eastern


def test_observation_time_requires_exactly_zero_utc_offset(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    common = dict(
        authority=ExternalOrderAuthority("authority"),
        reference_time=OrderTerminalReferenceTime(
            datetime(2026, 8, 20, tzinfo=timezone.utc)
        ),
        submission=submission,
        cancelled=True,
        expired=False,
    )
    with pytest.raises(ExecutionDomainError):
        SupportingOrderTerminalEvidence(
            observed_at_utc=datetime(2026, 8, 20), **common
        )
    with pytest.raises(ExecutionDomainError):
        SupportingOrderTerminalEvidence(
            observed_at_utc=datetime(
                2026, 8, 20, tzinfo=timezone(timedelta(hours=1))
            ),
            **common,
        )
    assert SupportingOrderTerminalEvidence(
        observed_at_utc=datetime(2026, 8, 20, tzinfo=timezone.utc), **common
    )


@pytest.mark.parametrize(
    ("cancelled", "expired"), [(False, False), (True, True)]
)
def test_insufficient_or_contradictory_evidence_produces_no_terminal_fact(
    target: PortfolioState, cancelled: bool, expired: bool
) -> None:
    submission = _submission(target)
    terminal = None
    with pytest.raises(ExecutionDomainError):
        terminal = recognize_order_terminal_state(
            submission,
            _evidence(submission, cancelled=cancelled, expired=expired),
        )
    assert terminal is None


def test_recognition_requires_identical_submission(target: PortfolioState) -> None:
    submission = _submission(target)
    different_submission = _submission(target)
    with pytest.raises(ExecutionDomainError):
        recognize_order_terminal_state(submission, _evidence(different_submission))


@pytest.mark.parametrize("invalid", [None, object(), "submission"])
def test_recognition_rejects_invalid_submission(
    target: PortfolioState, invalid: object
) -> None:
    submission = _submission(target)
    with pytest.raises(ExecutionDomainError):
        recognize_order_terminal_state(invalid, _evidence(submission))  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [None, object(), "evidence"])
def test_recognition_rejects_invalid_evidence(
    target: PortfolioState, invalid: object
) -> None:
    with pytest.raises(ExecutionDomainError):
        recognize_order_terminal_state(_submission(target), invalid)  # type: ignore[arg-type]


def test_contracts_are_minimal_immutable_and_controlled(target: PortfolioState) -> None:
    submission = _submission(target)
    evidence = _evidence(submission)
    terminal = recognize_order_terminal_state(submission, evidence)
    assert [field.name for field in fields(SupportingOrderTerminalEvidence)] == [
        "authority",
        "reference_time",
        "observed_at_utc",
        "submission",
        "cancelled",
        "expired",
    ]
    assert [field.name for field in fields(ExternalOrderTerminalState)] == [
        "submission",
        "state",
        "supporting_evidence",
    ]
    with pytest.raises(ExecutionDomainError):
        ExternalOrderTerminalState()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        terminal.state = OrderTerminalState.EXPIRED  # type: ignore[misc]
    assert evidence.submission is submission


def test_only_cancelled_and_expired_are_terminal_states() -> None:
    assert tuple(OrderTerminalState) == (
        OrderTerminalState.CANCELLED,
        OrderTerminalState.EXPIRED,
    )
    for unsupported in ("UNKNOWN", "PENDING", "REJECTED", "RECONCILED"):
        with pytest.raises(ValueError):
            OrderTerminalState(unsupported)
