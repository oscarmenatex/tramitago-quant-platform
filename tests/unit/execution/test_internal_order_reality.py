from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderAuthority,
    InternalOrderReality,
    InternalOrderRealityAuthority,
    OrderLifecycleMeaning,
    OrderRealityReferenceTime,
    OrderTerminalReferenceTime,
    SupportingInternalOrderRealityEvidence,
    SupportingOrderTerminalEvidence,
    prepare_operational_request,
    qualify_internal_order_reality,
    recognize_order_terminal_state,
)
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioState


UTC_TIME = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)


class IndeterminableTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def submission(target: PortfolioState) -> OperationalSubmission:
    return OperationalSubmission(prepare_operational_request(target))


def admission(
    source: OperationalSubmission, decision: AdmissionDecision
) -> OperationalAdmission:
    return OperationalAdmission(source, decision)


def terminal(source: OperationalSubmission, *, cancelled: bool):
    evidence = SupportingOrderTerminalEvidence(
        ExternalOrderAuthority("venue"),
        OrderTerminalReferenceTime(UTC_TIME),
        UTC_TIME,
        source,
        cancelled,
        not cancelled,
    )
    return recognize_order_terminal_state(source, evidence)


def evidence(
    source: OperationalSubmission,
    meanings: frozenset[OrderLifecycleMeaning] = frozenset(),
    facts: tuple = (),
    *,
    authority: str = "ledger",
    reference_time: OrderRealityReferenceTime | None = None,
    observed_at_utc: datetime = UTC_TIME,
) -> SupportingInternalOrderRealityEvidence:
    return SupportingInternalOrderRealityEvidence(
        InternalOrderRealityAuthority(authority),
        reference_time or OrderRealityReferenceTime(UTC_TIME),
        observed_at_utc,
        source,
        meanings,
        facts,
    )


def test_known_empty_snapshot_is_complete(target: PortfolioState) -> None:
    source = submission(target)
    item = evidence(source)

    reality = qualify_internal_order_reality([item])

    assert reality.submission is source
    assert reality.meanings == frozenset()
    assert reality.supporting_evidence == (item,)


@pytest.mark.parametrize(
    ("meaning", "fact_factory"),
    [
        (
            OrderLifecycleMeaning.ADMITTED,
            lambda source: admission(source, AdmissionDecision.ADMITTED),
        ),
        (
            OrderLifecycleMeaning.REJECTED,
            lambda source: admission(source, AdmissionDecision.REJECTED),
        ),
        (
            OrderLifecycleMeaning.CANCELLED,
            lambda source: terminal(source, cancelled=True),
        ),
        (
            OrderLifecycleMeaning.EXPIRED,
            lambda source: terminal(source, cancelled=False),
        ),
    ],
)
def test_each_meaning_has_exact_public_provenance(
    target: PortfolioState, meaning, fact_factory
) -> None:
    source = submission(target)
    fact = fact_factory(source)
    item = evidence(source, frozenset({meaning}), (fact,))

    reality = qualify_internal_order_reality((item,))

    assert reality.meanings == frozenset({meaning})
    assert reality.supporting_evidence[0] is item
    assert reality.supporting_evidence[0].supporting_facts[0] is fact


def test_multiple_meanings_and_duplicate_provenance_are_preserved(
    target: PortfolioState,
) -> None:
    source = submission(target)
    first = admission(source, AdmissionDecision.ADMITTED)
    duplicate = admission(source, AdmissionDecision.ADMITTED)
    cancelled = terminal(source, cancelled=True)
    meanings = frozenset(
        {OrderLifecycleMeaning.ADMITTED, OrderLifecycleMeaning.CANCELLED}
    )

    reality = qualify_internal_order_reality(
        (evidence(source, meanings, (first, duplicate, cancelled)),)
    )

    assert reality.meanings == meanings
    assert reality.supporting_evidence[0].supporting_facts == (
        first,
        duplicate,
        cancelled,
    )


def test_distinct_authorities_and_observation_times_are_compatible(
    target: PortfolioState,
) -> None:
    source = submission(target)
    fact = admission(source, AdmissionDecision.ADMITTED)
    meanings = frozenset({OrderLifecycleMeaning.ADMITTED})
    first = evidence(source, meanings, (fact,), authority="ledger")
    equivalent_time = OrderRealityReferenceTime(
        UTC_TIME.astimezone(timezone(timedelta(hours=-4)))
    )
    second = evidence(
        source,
        meanings,
        (fact,),
        authority="journal",
        reference_time=equivalent_time,
        observed_at_utc=UTC_TIME + timedelta(minutes=5),
    )

    reality = qualify_internal_order_reality((first, second))

    assert reality.supporting_evidence == (first, second)
    assert not hasattr(reality, "authority")


@pytest.mark.parametrize("value", ["", "   ", None, 7])
def test_invalid_authority_is_rejected(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        InternalOrderRealityAuthority(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "observed",
    [
        datetime(2026, 8, 20),
        datetime(2026, 8, 20, tzinfo=IndeterminableTimezone()),
        datetime(2026, 8, 20, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_observed_at_requires_exact_utc(
    target: PortfolioState, observed: datetime
) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(submission(target), observed_at_utc=observed)


def test_evidence_rejects_invalid_contract_values(target: PortfolioState) -> None:
    source = submission(target)
    valid = evidence(source)
    replacements = (
        {"authority": object()},
        {"reference_time": object()},
        {"submission": object()},
        {"meanings": set()},
        {"meanings": frozenset({"ADMITTED"})},
        {"supporting_facts": []},
        {"supporting_facts": (object(),)},
    )
    for replacement in replacements:
        values = {
            "authority": valid.authority,
            "reference_time": valid.reference_time,
            "observed_at_utc": valid.observed_at_utc,
            "submission": valid.submission,
            "meanings": valid.meanings,
            "supporting_facts": valid.supporting_facts,
        }
        values.update(replacement)
        with pytest.raises(ExecutionDomainError):
            SupportingInternalOrderRealityEvidence(**values)  # type: ignore[arg-type]


def test_meaning_provenance_is_total_and_has_no_orphans(
    target: PortfolioState,
) -> None:
    source = submission(target)
    admitted = admission(source, AdmissionDecision.ADMITTED)
    with pytest.raises(ExecutionDomainError):
        evidence(source, frozenset({OrderLifecycleMeaning.ADMITTED}), ())
    with pytest.raises(ExecutionDomainError):
        evidence(source, frozenset(), (admitted,))
    with pytest.raises(ExecutionDomainError):
        evidence(source, frozenset({OrderLifecycleMeaning.REJECTED}), (admitted,))


def test_fact_must_preserve_submission_identity(target: PortfolioState) -> None:
    first = submission(target)
    second = submission(target)
    assert first == second and first is not second
    fact = admission(second, AdmissionDecision.ADMITTED)
    with pytest.raises(ExecutionDomainError):
        evidence(first, frozenset({OrderLifecycleMeaning.ADMITTED}), (fact,))


def test_qualification_rejects_invalid_or_incompatible_evidence(
    target: PortfolioState,
) -> None:
    source = submission(target)
    other = submission(target)
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality(())
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality(None)  # type: ignore[arg-type]
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality((object(),))  # type: ignore[arg-type]
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality((evidence(source), evidence(other)))
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality(
            (
                evidence(source),
                evidence(
                    source,
                    reference_time=OrderRealityReferenceTime(
                        UTC_TIME + timedelta(seconds=1)
                    ),
                ),
            )
        )
    admitted = admission(source, AdmissionDecision.ADMITTED)
    with pytest.raises(ExecutionDomainError):
        qualify_internal_order_reality(
            (
                evidence(source),
                evidence(
                    source,
                    frozenset({OrderLifecycleMeaning.ADMITTED}),
                    (admitted,),
                ),
            )
        )


def test_contracts_are_exact_immutable_and_controlled(
    target: PortfolioState,
) -> None:
    source = submission(target)
    reality = qualify_internal_order_reality((evidence(source),))

    assert [item.name for item in fields(InternalOrderRealityAuthority)] == ["value"]
    assert [item.name for item in fields(SupportingInternalOrderRealityEvidence)] == [
        "authority",
        "reference_time",
        "observed_at_utc",
        "submission",
        "meanings",
        "supporting_facts",
    ]
    assert [item.name for item in fields(InternalOrderReality)] == [
        "reference_time",
        "submission",
        "meanings",
        "supporting_evidence",
    ]
    with pytest.raises(ExecutionDomainError):
        InternalOrderReality()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        reality.meanings = frozenset()  # type: ignore[misc]


def test_later_snapshot_does_not_change_prior_snapshot(target: PortfolioState) -> None:
    source = submission(target)
    original = qualify_internal_order_reality((evidence(source),))
    fact = admission(source, AdmissionDecision.ADMITTED)
    later = qualify_internal_order_reality(
        (
            evidence(
                source,
                frozenset({OrderLifecycleMeaning.ADMITTED}),
                (fact,),
            ),
        )
    )
    assert original.meanings == frozenset()
    assert later.meanings == frozenset({OrderLifecycleMeaning.ADMITTED})
