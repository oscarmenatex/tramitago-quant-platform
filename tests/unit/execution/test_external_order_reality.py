from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderReality,
    ExternalOrderRealityAuthority,
    OrderLifecycleMeaning,
    OrderRealityReferenceTime,
    SupportingExternalOrderRealityEvidence,
    prepare_operational_request,
    qualify_external_order_reality,
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
    authority: ExternalOrderRealityAuthority | None = None,
    reference_time: OrderRealityReferenceTime | None = None,
    observed_at_utc: datetime | None = None,
    meanings: frozenset[OrderLifecycleMeaning] = frozenset(),
) -> SupportingExternalOrderRealityEvidence:
    return SupportingExternalOrderRealityEvidence(
        authority=authority or ExternalOrderRealityAuthority("opaque authority"),
        reference_time=reference_time
        or OrderRealityReferenceTime(datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc)),
        observed_at_utc=observed_at_utc
        or datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc),
        submission=submission,
        meanings=meanings,
    )


@pytest.mark.parametrize(
    "meanings",
    [
        frozenset(),
        frozenset({OrderLifecycleMeaning.ADMITTED}),
        frozenset({OrderLifecycleMeaning.REJECTED}),
        frozenset({OrderLifecycleMeaning.CANCELLED}),
        frozenset({OrderLifecycleMeaning.EXPIRED}),
        frozenset({OrderLifecycleMeaning.ADMITTED, OrderLifecycleMeaning.CANCELLED}),
    ],
)
def test_qualifies_each_complete_lifecycle_meaning_snapshot(
    target: PortfolioState,
    meanings: frozenset[OrderLifecycleMeaning],
) -> None:
    submission = _submission(target)
    evidence = _evidence(submission, meanings=meanings)

    reality = qualify_external_order_reality([evidence])

    assert reality.authority is evidence.authority
    assert reality.reference_time is evidence.reference_time
    assert reality.submission is submission
    assert reality.meanings is meanings
    assert reality.supporting_evidence == (evidence,)
    assert reality.supporting_evidence[0] is evidence


def test_compatible_evidence_preserves_all_observation_provenance(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    authority = ExternalOrderRealityAuthority("venue/account")
    reference_time = OrderRealityReferenceTime(
        datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc)
    )
    meanings = frozenset({OrderLifecycleMeaning.ADMITTED})
    first = _evidence(
        submission,
        authority=authority,
        reference_time=reference_time,
        observed_at_utc=datetime(2026, 8, 20, 3, 0, tzinfo=timezone.utc),
        meanings=meanings,
    )
    second = _evidence(
        submission,
        authority=authority,
        reference_time=reference_time,
        observed_at_utc=datetime(2026, 8, 20, 4, 0, tzinfo=timezone.utc),
        meanings=meanings,
    )

    reality = qualify_external_order_reality((first, second))

    assert reality.supporting_evidence == (first, second)
    assert reality.supporting_evidence[0] is first
    assert reality.supporting_evidence[1] is second


@pytest.mark.parametrize("value", ["venue-7", " account / channel ", "opaque:1"])
def test_authority_accepts_explicit_non_empty_opaque_text(value: str) -> None:
    assert ExternalOrderRealityAuthority(value).value == value


@pytest.mark.parametrize("value", ["", "   ", None, 7])
def test_authority_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalOrderRealityAuthority(value)  # type: ignore[arg-type]


def test_reference_time_requires_a_determinable_offset() -> None:
    with pytest.raises(ExecutionDomainError):
        OrderRealityReferenceTime(datetime(2026, 8, 20))
    with pytest.raises(ExecutionDomainError):
        OrderRealityReferenceTime(
            datetime(2026, 8, 20, tzinfo=IndeterminableTimezone())
        )


def test_equivalent_reference_instants_with_different_offsets_are_compatible(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    utc = OrderRealityReferenceTime(datetime(2026, 8, 20, 2, 0, tzinfo=timezone.utc))
    eastern = OrderRealityReferenceTime(
        datetime(2026, 8, 19, 22, 0, tzinfo=timezone(timedelta(hours=-4)))
    )

    reality = qualify_external_order_reality(
        (
            _evidence(submission, reference_time=utc),
            _evidence(submission, reference_time=eastern),
        )
    )

    assert reality.reference_time is utc


def test_observed_at_utc_requires_an_exact_zero_offset(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    for invalid in (
        datetime(2026, 8, 20),
        datetime(2026, 8, 20, tzinfo=IndeterminableTimezone()),
        datetime(2026, 8, 20, tzinfo=timezone(timedelta(hours=1))),
    ):
        with pytest.raises(ExecutionDomainError):
            _evidence(submission, observed_at_utc=invalid)


def test_evidence_rejects_invalid_submission_and_meanings(
    target: PortfolioState,
) -> None:
    valid = _evidence(_submission(target))
    with pytest.raises(ExecutionDomainError):
        SupportingExternalOrderRealityEvidence(
            valid.authority,
            valid.reference_time,
            valid.observed_at_utc,
            object(),  # type: ignore[arg-type]
            valid.meanings,
        )
    for invalid in (
        set(),
        frozenset({"ADMITTED"}),
        frozenset({OrderLifecycleMeaning.ADMITTED, "CANCELLED"}),
    ):
        with pytest.raises(ExecutionDomainError):
            SupportingExternalOrderRealityEvidence(
                valid.authority,
                valid.reference_time,
                valid.observed_at_utc,
                valid.submission,
                invalid,  # type: ignore[arg-type]
            )


@pytest.mark.parametrize("invalid", [None, 7, object()])
def test_qualification_rejects_non_iterable_or_invalid_evidence(
    target: PortfolioState, invalid: object
) -> None:
    with pytest.raises(ExecutionDomainError):
        qualify_external_order_reality(invalid)  # type: ignore[arg-type]
    with pytest.raises(ExecutionDomainError):
        qualify_external_order_reality([_evidence(_submission(target)), invalid])  # type: ignore[list-item]


def test_zero_evidence_publishes_no_reality() -> None:
    reality = None
    with pytest.raises(ExecutionDomainError):
        reality = qualify_external_order_reality([])
    assert reality is None


def test_incompatible_authority_is_rejected(target: PortfolioState) -> None:
    submission = _submission(target)
    with pytest.raises(ExecutionDomainError):
        qualify_external_order_reality(
            (
                _evidence(submission),
                _evidence(
                    submission,
                    authority=ExternalOrderRealityAuthority("different"),
                ),
            )
        )


def test_structurally_equal_but_distinct_submission_is_rejected(
    target: PortfolioState,
) -> None:
    first = _submission(target)
    second = _submission(target)
    assert first == second
    assert first is not second
    with pytest.raises(ExecutionDomainError):
        qualify_external_order_reality((_evidence(first), _evidence(second)))


def test_distinct_reference_instants_are_rejected(target: PortfolioState) -> None:
    submission = _submission(target)
    later = OrderRealityReferenceTime(
        datetime(2026, 8, 20, 2, 0, 1, tzinfo=timezone.utc)
    )
    with pytest.raises(ExecutionDomainError):
        qualify_external_order_reality(
            (_evidence(submission), _evidence(submission, reference_time=later))
        )


def test_different_complete_meanings_are_rejected_without_combining(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    admitted = _evidence(
        submission, meanings=frozenset({OrderLifecycleMeaning.ADMITTED})
    )
    cancelled = _evidence(
        submission, meanings=frozenset({OrderLifecycleMeaning.CANCELLED})
    )
    reality = None
    with pytest.raises(ExecutionDomainError):
        reality = qualify_external_order_reality((admitted, cancelled))
    assert reality is None


def test_contracts_are_exact_immutable_and_controlled(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    evidence = _evidence(submission)
    reality = qualify_external_order_reality([evidence])

    assert tuple(OrderLifecycleMeaning) == (
        OrderLifecycleMeaning.ADMITTED,
        OrderLifecycleMeaning.REJECTED,
        OrderLifecycleMeaning.CANCELLED,
        OrderLifecycleMeaning.EXPIRED,
    )
    assert [field.name for field in fields(ExternalOrderRealityAuthority)] == ["value"]
    assert [field.name for field in fields(OrderRealityReferenceTime)] == ["value"]
    assert [field.name for field in fields(SupportingExternalOrderRealityEvidence)] == [
        "authority",
        "reference_time",
        "observed_at_utc",
        "submission",
        "meanings",
    ]
    assert [field.name for field in fields(ExternalOrderReality)] == [
        "authority",
        "reference_time",
        "submission",
        "meanings",
        "supporting_evidence",
    ]
    with pytest.raises(ExecutionDomainError):
        ExternalOrderReality()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        reality.meanings = frozenset({OrderLifecycleMeaning.EXPIRED})  # type: ignore[misc]


def test_qualified_snapshot_is_not_changed_by_later_observations(
    target: PortfolioState,
) -> None:
    submission = _submission(target)
    original = qualify_external_order_reality([_evidence(submission)])
    later = qualify_external_order_reality(
        [
            _evidence(
                submission,
                meanings=frozenset({OrderLifecycleMeaning.EXPIRED}),
                observed_at_utc=datetime(2026, 8, 21, tzinfo=timezone.utc),
            )
        ]
    )

    assert original.meanings == frozenset()
    assert later.meanings == frozenset({OrderLifecycleMeaning.EXPIRED})
