from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime,
    ExternalEconomicAuthority,
    ExternalEconomicObservationDomainError,
    ExternallyObservedEconomicReality,
    MonetaryCoverage,
    ObservedMonetaryAssertion,
    ObservedPositionAssertion,
    PositionCoverage,
    SupportingEconomicEvidence,
    observe_external_economic_reality,
)


def evidence(authority, reference_time, **changes):
    values = {
        "authority": authority,
        "reference_time": reference_time,
        "position_coverage": PositionCoverage.partial(),
        "monetary_coverage": MonetaryCoverage.partial(),
        "observed_positions": (),
        "observed_monetary_balances": (),
    }
    values.update(changes)
    return SupportingEconomicEvidence(**values)


@pytest.mark.parametrize("quantity", [Decimal("10"), Decimal("0"), Decimal("-10")])
def test_observed_position_preserves_signed_and_explicit_zero_values(
    authority, reference_time, quantity
):
    instrument = InstrumentReference("figi", "AAPL")
    assertion = ObservedPositionAssertion(instrument, quantity)
    reality = observe_external_economic_reality(
        [
            evidence(
                authority,
                reference_time,
                position_coverage=PositionCoverage.partial([instrument]),
                observed_positions=[assertion],
            )
        ]
    )
    assert reality.observed_positions == (assertion,)


@pytest.mark.parametrize("amount", [Decimal("500"), Decimal("0"), Decimal("-500")])
def test_observed_monetary_balance_preserves_signed_and_explicit_zero_values(
    authority, reference_time, amount
):
    currency = CurrencyReference("usd")
    assertion = ObservedMonetaryAssertion(currency, amount)
    reality = observe_external_economic_reality(
        [
            evidence(
                authority,
                reference_time,
                monetary_coverage=MonetaryCoverage.partial([currency]),
                observed_monetary_balances=[assertion],
            )
        ]
    )
    assert reality.observed_monetary_balances == (assertion,)


def test_multiple_compatible_evidence_is_order_independent_and_preserves_provenance(
    authority, reference_time
):
    instrument = InstrumentReference("figi", "AAPL")
    currency = CurrencyReference("USD")
    first = evidence(
        authority,
        reference_time,
        position_coverage=PositionCoverage.partial([instrument]),
        observed_positions=[ObservedPositionAssertion(instrument, Decimal("10"))],
    )
    second = evidence(
        authority,
        reference_time,
        monetary_coverage=MonetaryCoverage.partial([currency]),
        observed_monetary_balances=[ObservedMonetaryAssertion(currency, Decimal("5"))],
    )
    left = observe_external_economic_reality([first, second])
    right = observe_external_economic_reality([second, first])
    assert left == right
    assert left.supporting_evidence == right.supporting_evidence
    assert len(left.supporting_evidence) == 2


def test_assertion_order_is_non_semantic(authority, reference_time):
    a = InstrumentReference("figi", "A")
    b = InstrumentReference("figi", "B")
    assertions = [
        ObservedPositionAssertion(a, Decimal("1")),
        ObservedPositionAssertion(b, Decimal("2")),
    ]
    first = evidence(
        authority,
        reference_time,
        position_coverage=PositionCoverage.partial([a, b]),
        observed_positions=assertions,
    )
    second = evidence(
        authority,
        reference_time,
        position_coverage=PositionCoverage.partial([a, b]),
        observed_positions=reversed(assertions),
    )
    assert first == second


def test_different_authorities_are_incompatible(authority, reference_time):
    instrument = InstrumentReference("figi", "A")
    values = dict(
        position_coverage=PositionCoverage.partial([instrument]),
        observed_positions=[ObservedPositionAssertion(instrument, Decimal("1"))],
    )
    with pytest.raises(ExternalEconomicObservationDomainError):
        observe_external_economic_reality(
            [
                evidence(authority, reference_time, **values),
                evidence(ExternalEconomicAuthority("other"), reference_time, **values),
            ]
        )


def test_incompatible_temporal_references_are_rejected(authority, reference_time):
    later = EconomicRealityReferenceTime(
        reference_time.value + timedelta(seconds=1)
    )
    with pytest.raises(ExternalEconomicObservationDomainError):
        observe_external_economic_reality(
            [
                evidence(authority, reference_time, position_coverage=PositionCoverage.complete()),
                evidence(authority, later, monetary_coverage=MonetaryCoverage.complete()),
            ]
        )


def test_equivalent_instants_with_different_offsets_have_same_public_meaning(
    authority,
):
    utc_reference = EconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, 0, tzinfo=timezone.utc)
    )
    utc_minus_four_reference = EconomicRealityReferenceTime(
        datetime(
            2026,
            8,
            12,
            12,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        )
    )
    assert utc_reference == utc_minus_four_reference
    assert hash(utc_reference) == hash(utc_minus_four_reference)

    position_evidence = evidence(
        authority,
        utc_reference,
        position_coverage=PositionCoverage.complete(),
    )
    monetary_evidence = evidence(
        authority,
        utc_minus_four_reference,
        monetary_coverage=MonetaryCoverage.complete(),
    )
    reality = observe_external_economic_reality(
        [position_evidence, monetary_evidence]
    )

    assert isinstance(reality, ExternallyObservedEconomicReality)
    assert reality.reference_time == utc_reference
    assert reality.reference_time == utc_minus_four_reference


@pytest.mark.parametrize(
    ("identity", "assertion", "coverage", "keyword"),
    [
        (
            InstrumentReference("figi", "A"),
            ObservedPositionAssertion,
            PositionCoverage,
            "observed_positions",
        ),
        (
            CurrencyReference("USD"),
            ObservedMonetaryAssertion,
            MonetaryCoverage,
            "observed_monetary_balances",
        ),
    ],
)
def test_contradictory_evidence_is_rejected(
    authority, reference_time, identity, assertion, coverage, keyword
):
    coverage_keyword = (
        "position_coverage" if keyword == "observed_positions" else "monetary_coverage"
    )
    first = evidence(
        authority,
        reference_time,
        **{coverage_keyword: coverage.partial([identity]), keyword: [assertion(identity, Decimal("1"))]},
    )
    second = evidence(
        authority,
        reference_time,
        **{coverage_keyword: coverage.partial([identity]), keyword: [assertion(identity, Decimal("2"))]},
    )
    with pytest.raises(ExternalEconomicObservationDomainError):
        observe_external_economic_reality([first, second])


def test_partial_absence_is_not_zero_and_complete_absence_is_meaningful(
    authority, reference_time
):
    instrument = InstrumentReference("figi", "A")
    partial = observe_external_economic_reality(
        [evidence(authority, reference_time, monetary_coverage=MonetaryCoverage.complete())]
    )
    complete = observe_external_economic_reality(
        [evidence(authority, reference_time, position_coverage=PositionCoverage.complete())]
    )
    assert not partial.position_coverage.covers(instrument)
    assert partial.observed_positions == ()
    assert complete.position_coverage.covers(instrument)
    assert complete.observed_positions == ()


def test_explicit_zero_differs_from_complete_coverage_absence(authority, reference_time):
    instrument = InstrumentReference("figi", "A")
    absent = observe_external_economic_reality(
        [evidence(authority, reference_time, position_coverage=PositionCoverage.complete())]
    )
    explicit = observe_external_economic_reality(
        [
            evidence(
                authority,
                reference_time,
                position_coverage=PositionCoverage.complete(),
                observed_positions=[ObservedPositionAssertion(instrument, Decimal("0"))],
            )
        ]
    )
    assert absent != explicit
    assert explicit.observed_positions[0].quantity.is_zero()


def test_complete_coverage_allows_economically_empty_observation(authority, reference_time):
    reality = observe_external_economic_reality(
        [
            evidence(
                authority,
                reference_time,
                position_coverage=PositionCoverage.complete(),
                monetary_coverage=MonetaryCoverage.complete(),
            )
        ]
    )
    assert reality.observed_positions == reality.observed_monetary_balances == ()


def test_no_assertions_and_no_meaningful_coverage_is_rejected(authority, reference_time):
    with pytest.raises(ExternalEconomicObservationDomainError):
        evidence(authority, reference_time)


def test_source_and_published_reality_are_immutable_and_stable(authority, reference_time):
    source = evidence(authority, reference_time, position_coverage=PositionCoverage.complete())
    published = observe_external_economic_reality([source])
    observe_external_economic_reality(
        [evidence(authority, reference_time, monetary_coverage=MonetaryCoverage.complete())]
    )
    assert published.supporting_evidence == (source,)
    with pytest.raises(FrozenInstanceError):
        source.authority = ExternalEconomicAuthority("changed")


def test_public_construction_cannot_bypass_reality_invariants():
    with pytest.raises(ExternalEconomicObservationDomainError):
        ExternallyObservedEconomicReality()


def test_temporal_reference_rejects_implicit_timezone():
    with pytest.raises(ExternalEconomicObservationDomainError):
        EconomicRealityReferenceTime(datetime(2026, 1, 1))


def test_invalid_and_non_finite_numbers_are_rejected():
    instrument = InstrumentReference("figi", "A")
    with pytest.raises(ExternalEconomicObservationDomainError):
        ObservedPositionAssertion(instrument, Decimal("NaN"))
    with pytest.raises(ExternalEconomicObservationDomainError):
        ObservedPositionAssertion(instrument, 1)


def test_evidence_cannot_publish_assertions_beyond_partial_coverage(
    authority, reference_time
):
    instrument = InstrumentReference("figi", "A")
    with pytest.raises(ExternalEconomicObservationDomainError):
        evidence(
            authority,
            reference_time,
            position_coverage=PositionCoverage.partial(),
            observed_positions=[ObservedPositionAssertion(instrument, Decimal("1"))],
        )
