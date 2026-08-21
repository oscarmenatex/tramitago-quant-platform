from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderAuthority,
    ExternalOrderRealityAuthority,
    InternalOrderRealityAuthority,
    OrderLifecycleMeaning,
    OrderRealityReferenceTime,
    OrderRealityVerification,
    OrderRealityVerificationOutcome,
    OrderTerminalReferenceTime,
    SupportingExternalOrderRealityEvidence,
    SupportingInternalOrderRealityEvidence,
    SupportingOrderTerminalEvidence,
    prepare_operational_request,
    qualify_external_order_reality,
    qualify_internal_order_reality,
    recognize_order_terminal_state,
    verify_order_reality,
)
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioState


UTC_TIME = datetime(2026, 8, 21, 12, tzinfo=timezone.utc)


def _submission(target: PortfolioState) -> OperationalSubmission:
    return OperationalSubmission(prepare_operational_request(target))


def _facts(source: OperationalSubmission, meanings: frozenset[OrderLifecycleMeaning]):
    facts = []
    if OrderLifecycleMeaning.ADMITTED in meanings:
        facts.append(OperationalAdmission(source, AdmissionDecision.ADMITTED))
    if OrderLifecycleMeaning.REJECTED in meanings:
        facts.append(OperationalAdmission(source, AdmissionDecision.REJECTED))
    for meaning, cancelled in (
        (OrderLifecycleMeaning.CANCELLED, True),
        (OrderLifecycleMeaning.EXPIRED, False),
    ):
        if meaning in meanings:
            facts.append(
                recognize_order_terminal_state(
                    source,
                    SupportingOrderTerminalEvidence(
                        ExternalOrderAuthority("venue"),
                        OrderTerminalReferenceTime(UTC_TIME),
                        UTC_TIME,
                        source,
                        cancelled,
                        not cancelled,
                    ),
                )
            )
    return tuple(facts)


def _realities(
    source: OperationalSubmission,
    internal_meanings: frozenset[OrderLifecycleMeaning],
    external_meanings: frozenset[OrderLifecycleMeaning],
    *,
    internal_time: OrderRealityReferenceTime | None = None,
    external_time: OrderRealityReferenceTime | None = None,
):
    internal = qualify_internal_order_reality(
        (
            SupportingInternalOrderRealityEvidence(
                InternalOrderRealityAuthority("internal ledger"),
                internal_time or OrderRealityReferenceTime(UTC_TIME),
                UTC_TIME,
                source,
                internal_meanings,
                _facts(source, internal_meanings),
            ),
        )
    )
    external = qualify_external_order_reality(
        (
            SupportingExternalOrderRealityEvidence(
                ExternalOrderRealityAuthority("broker account"),
                external_time or OrderRealityReferenceTime(UTC_TIME),
                UTC_TIME + timedelta(hours=1),
                source,
                external_meanings,
            ),
        )
    )
    return internal, external


@pytest.mark.parametrize(
    "meanings",
    [
        frozenset(),
        frozenset({OrderLifecycleMeaning.ADMITTED}),
        frozenset({OrderLifecycleMeaning.ADMITTED, OrderLifecycleMeaning.CANCELLED}),
    ],
)
def test_exact_meanings_set_agreement(target: PortfolioState, meanings) -> None:
    internal, external = _realities(_submission(target), meanings, meanings)
    verification = verify_order_reality(internal, external)
    assert verification.outcome is OrderRealityVerificationOutcome.AGREEMENT
    assert verification.internal_reality is internal
    assert verification.external_reality is external


@pytest.mark.parametrize(
    ("internal_meanings", "external_meanings"),
    [
        (frozenset(), frozenset({OrderLifecycleMeaning.ADMITTED})),
        (
            frozenset({OrderLifecycleMeaning.ADMITTED}),
            frozenset({OrderLifecycleMeaning.REJECTED}),
        ),
        (
            frozenset({OrderLifecycleMeaning.CANCELLED}),
            frozenset({OrderLifecycleMeaning.EXPIRED}),
        ),
        (
            frozenset(
                {OrderLifecycleMeaning.ADMITTED, OrderLifecycleMeaning.CANCELLED}
            ),
            frozenset({OrderLifecycleMeaning.ADMITTED}),
        ),
    ],
)
def test_exact_meanings_set_discrepancy(
    target: PortfolioState, internal_meanings, external_meanings
) -> None:
    realities = _realities(_submission(target), internal_meanings, external_meanings)
    assert (
        verify_order_reality(*realities).outcome
        is OrderRealityVerificationOutcome.DISCREPANCY
    )


def test_provenance_and_authority_do_not_affect_agreement(
    target: PortfolioState,
) -> None:
    source = _submission(target)
    meanings = frozenset({OrderLifecycleMeaning.ADMITTED})
    internal, external = _realities(source, meanings, meanings)
    assert internal.supporting_evidence[0].authority != external.authority
    assert (
        internal.supporting_evidence[0].observed_at_utc
        != external.supporting_evidence[0].observed_at_utc
    )
    assert (
        verify_order_reality(internal, external).outcome
        is OrderRealityVerificationOutcome.AGREEMENT
    )


def test_submission_comparability_requires_identity(target: PortfolioState) -> None:
    first = _submission(target)
    second = _submission(target)
    assert first == second and first is not second
    internal, _ = _realities(first, frozenset(), frozenset())
    _, external = _realities(second, frozenset(), frozenset())
    with pytest.raises(ExecutionDomainError):
        verify_order_reality(internal, external)


def test_equivalent_reference_time_offsets_are_comparable(
    target: PortfolioState,
) -> None:
    utc = OrderRealityReferenceTime(UTC_TIME)
    eastern = OrderRealityReferenceTime(
        UTC_TIME.astimezone(timezone(timedelta(hours=-4)))
    )
    realities = _realities(
        _submission(target),
        frozenset(),
        frozenset(),
        internal_time=utc,
        external_time=eastern,
    )
    assert (
        verify_order_reality(*realities).outcome
        is OrderRealityVerificationOutcome.AGREEMENT
    )


def test_different_reference_times_are_rejected(target: PortfolioState) -> None:
    realities = _realities(
        _submission(target),
        frozenset(),
        frozenset(),
        external_time=OrderRealityReferenceTime(UTC_TIME + timedelta(seconds=1)),
    )
    with pytest.raises(ExecutionDomainError):
        verify_order_reality(*realities)


@pytest.mark.parametrize("position", [0, 1])
def test_invalid_input_type_is_rejected(target: PortfolioState, position: int) -> None:
    realities = list(_realities(_submission(target), frozenset(), frozenset()))
    realities[position] = object()
    with pytest.raises(ExecutionDomainError):
        verify_order_reality(*realities)  # type: ignore[arg-type]


def test_contract_is_exact_controlled_and_immutable(target: PortfolioState) -> None:
    assert tuple(OrderRealityVerificationOutcome) == (
        OrderRealityVerificationOutcome.AGREEMENT,
        OrderRealityVerificationOutcome.DISCREPANCY,
    )
    assert [field.name for field in fields(OrderRealityVerification)] == [
        "internal_reality",
        "external_reality",
        "outcome",
    ]
    with pytest.raises(ExecutionDomainError):
        OrderRealityVerification()
    verification = verify_order_reality(
        *_realities(_submission(target), frozenset(), frozenset())
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        verification.outcome = OrderRealityVerificationOutcome.DISCREPANCY  # type: ignore[misc]
