from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import (
    EconomicRealityDimension,
    EconomicRealityVerification,
    EconomicRealityVerificationDomainError,
    EconomicRealityVerificationOutcome as Outcome,
    EconomicRealityVerificationResult,
    verify_economic_reality,
)
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime,
    ExternalEconomicAuthority,
    MonetaryCoverage,
    ObservedMonetaryAssertion,
    ObservedPositionAssertion,
    PositionCoverage,
    SupportingEconomicEvidence,
    observe_external_economic_reality,
)
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence,
    InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime,
    qualify_internal_economic_reality,
)
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


AAPL = InstrumentReference("FIGI", "AAPL")
MSFT = InstrumentReference("FIGI", "MSFT")
USD = CurrencyReference("USD")
EUR = CurrencyReference("EUR")
UTC_TIME = datetime(2026, 8, 12, 16, tzinfo=timezone.utc)


def internal(*, positions=(), monetary=(), when=UTC_TIME):
    state = PortfolioState(positions=positions, monetary_balances=monetary)
    evidence = InternalEconomicRealityEvidence(
        state,
        InternalEconomicRealityReferenceTime(when),
        InternalEconomicRealityProvenance("ledger"),
    )
    return qualify_internal_economic_reality((evidence,))


def external(
    *, positions=(), monetary=(), position_coverage=None,
    monetary_coverage=None, when=UTC_TIME,
):
    evidence = SupportingEconomicEvidence(
        authority=ExternalEconomicAuthority("custodian"),
        reference_time=EconomicRealityReferenceTime(when),
        position_coverage=position_coverage or PositionCoverage.partial(
            x.instrument for x in positions
        ),
        monetary_coverage=monetary_coverage or MonetaryCoverage.partial(
            x.currency for x in monetary
        ),
        observed_positions=positions,
        observed_monetary_balances=monetary,
    )
    return observe_external_economic_reality((evidence,))


def result_for(results, identity):
    return next(result for result in results if result.identity == identity)


@pytest.mark.parametrize(
    ("internal_value", "external_value", "expected"),
    [("10", "10", Outcome.AGREEMENT), ("10", "11", Outcome.DISCREPANCY)],
)
def test_position_comparison(internal_value, external_value, expected):
    verification = verify_economic_reality(
        internal(positions=(PortfolioPosition(AAPL, Decimal(internal_value)),)),
        external(positions=(ObservedPositionAssertion(AAPL, Decimal(external_value)),)),
    )
    result = result_for(verification.position_results, AAPL)
    assert result.outcome is expected
    assert (result.internal_value, result.external_value) == (
        Decimal(internal_value), Decimal(external_value)
    )


@pytest.mark.parametrize(
    ("internal_value", "external_value", "expected"),
    [("10", "10", Outcome.AGREEMENT), ("10", "11", Outcome.DISCREPANCY)],
)
def test_monetary_comparison(internal_value, external_value, expected):
    verification = verify_economic_reality(
        internal(monetary=(MonetaryBalance(USD, Decimal(internal_value)),)),
        external(monetary=(ObservedMonetaryAssertion(USD, Decimal(external_value)),)),
    )
    result = result_for(verification.monetary_results, USD)
    assert result.outcome is expected


def test_absence_zero_and_covered_absence_semantics():
    explicit = external(positions=(ObservedPositionAssertion(AAPL, Decimal(0)),))
    absent = external(position_coverage=PositionCoverage.partial((AAPL,)))
    explicit_result = result_for(
        verify_economic_reality(internal(), explicit).position_results, AAPL
    )
    absent_result = result_for(
        verify_economic_reality(internal(), absent).position_results, AAPL
    )
    assert explicit_result.outcome is absent_result.outcome is Outcome.AGREEMENT
    assert explicit != absent
    assert explicit.observed_positions and not absent.observed_positions


def test_covered_absence_disagrees_with_internal_material_value():
    verification = verify_economic_reality(
        internal(positions=(PortfolioPosition(AAPL, Decimal(10)),)),
        external(position_coverage=PositionCoverage.complete()),
    )
    result = result_for(verification.position_results, AAPL)
    assert result.outcome is Outcome.DISCREPANCY
    assert result.external_value == Decimal(0)


def test_internal_identity_outside_partial_coverage_is_not_comparable():
    verification = verify_economic_reality(
        internal(positions=(PortfolioPosition(MSFT, Decimal(5)),)),
        external(position_coverage=PositionCoverage.partial((AAPL,))),
    )
    result = result_for(verification.position_results, MSFT)
    assert result.outcome is Outcome.NOT_COMPARABLE
    assert result.external_value is None


def test_external_only_material_identity_is_discrepancy():
    verification = verify_economic_reality(
        internal(), external(positions=(ObservedPositionAssertion(AAPL, Decimal(5)),))
    )
    result = result_for(verification.position_results, AAPL)
    assert result.outcome is Outcome.DISCREPANCY
    assert result.internal_value == Decimal(0)


def test_mixed_results_and_source_preservation():
    left = internal(
        positions=(PortfolioPosition(AAPL, Decimal(5)), PortfolioPosition(MSFT, Decimal(3))),
        monetary=(MonetaryBalance(USD, Decimal(10)),),
    )
    right = external(
        positions=(ObservedPositionAssertion(AAPL, Decimal(5)),),
        monetary=(ObservedMonetaryAssertion(USD, Decimal(11)),),
        position_coverage=PositionCoverage.partial((AAPL,)),
    )
    verification = verify_economic_reality(left, right)
    assert verification.internal_reality is left
    assert verification.external_reality is right
    assert {x.outcome for x in verification.position_results} == {
        Outcome.AGREEMENT, Outcome.NOT_COMPARABLE
    }
    assert {x.outcome for x in verification.monetary_results} == {Outcome.DISCREPANCY}


def test_empty_verification_is_valid():
    verification = verify_economic_reality(
        internal(), external(position_coverage=PositionCoverage.complete())
    )
    assert verification.position_results == frozenset()
    assert verification.monetary_results == frozenset()


@pytest.mark.parametrize("bad", [None, object(), PortfolioState()])
def test_invalid_internal_input_is_domain_error(bad):
    with pytest.raises(EconomicRealityVerificationDomainError):
        verify_economic_reality(bad, external(position_coverage=PositionCoverage.complete()))


@pytest.mark.parametrize("bad", [None, object(), PortfolioState()])
def test_invalid_external_input_is_domain_error(bad):
    with pytest.raises(EconomicRealityVerificationDomainError):
        verify_economic_reality(internal(), bad)


def test_different_instants_are_error_not_not_comparable():
    with pytest.raises(EconomicRealityVerificationDomainError):
        verify_economic_reality(
            internal(),
            external(
                position_coverage=PositionCoverage.complete(),
                when=UTC_TIME + timedelta(seconds=1),
            ),
        )


def test_same_instant_with_different_offsets_is_valid():
    eastern = timezone(timedelta(hours=-4))
    verification = verify_economic_reality(
        internal(),
        external(
            position_coverage=PositionCoverage.complete(),
            when=datetime(2026, 8, 12, 12, tzinfo=eastern),
        ),
    )
    assert isinstance(verification, EconomicRealityVerification)


def test_unique_unordered_immutable_results_and_stable_previous_verification():
    left = internal(positions=(PortfolioPosition(AAPL, Decimal(1)),))
    first = verify_economic_reality(
        left, external(positions=(ObservedPositionAssertion(AAPL, Decimal(1)),))
    )
    snapshot = first.position_results
    verify_economic_reality(
        left, external(positions=(ObservedPositionAssertion(AAPL, Decimal(2)),))
    )
    assert first.position_results == snapshot
    assert len({(x.dimension, x.identity) for x in snapshot}) == len(snapshot)
    with pytest.raises((AttributeError, TypeError)):
        first.position_results.add("invalid")


def test_result_order_has_no_public_meaning():
    internal_positions = (
        PortfolioPosition(AAPL, Decimal(1)),
        PortfolioPosition(MSFT, Decimal(2)),
    )
    internal_monetary = (
        MonetaryBalance(USD, Decimal(10)),
        MonetaryBalance(EUR, Decimal(20)),
    )
    external_positions = (
        ObservedPositionAssertion(AAPL, Decimal(1)),
        ObservedPositionAssertion(MSFT, Decimal(3)),
    )
    external_monetary = (
        ObservedMonetaryAssertion(USD, Decimal(10)),
        ObservedMonetaryAssertion(EUR, Decimal(21)),
    )

    first = verify_economic_reality(
        internal(positions=internal_positions, monetary=internal_monetary),
        external(positions=external_positions, monetary=external_monetary),
    )
    reversed_order = verify_economic_reality(
        internal(
            positions=tuple(reversed(internal_positions)),
            monetary=tuple(reversed(internal_monetary)),
        ),
        external(
            positions=tuple(reversed(external_positions)),
            monetary=tuple(reversed(external_monetary)),
        ),
    )

    assert first == reversed_order
    assert first.position_results == reversed_order.position_results
    assert first.monetary_results == reversed_order.monetary_results


def test_result_dimensions_and_public_construction_are_guarded():
    verification = verify_economic_reality(
        internal(monetary=(MonetaryBalance(USD, Decimal(1)),)),
        external(monetary=(ObservedMonetaryAssertion(USD, Decimal(1)),)),
    )
    assert result_for(verification.monetary_results, USD).dimension is (
        EconomicRealityDimension.MONETARY_BALANCE
    )
    with pytest.raises(EconomicRealityVerificationDomainError):
        EconomicRealityVerification()
    with pytest.raises(EconomicRealityVerificationDomainError):
        EconomicRealityVerificationResult()
