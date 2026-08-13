from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.internal_economic_reality import (
    InternalEconomicReality,
    InternalEconomicRealityEvidence,
    InternalEconomicRealityProvenance,
    InternalEconomicRealityQualificationDomainError,
    InternalEconomicRealityReferenceTime,
    qualify_internal_economic_reality,
)
from quant_platform.portfolio import PortfolioState


def test_non_empty_portfolio_state_qualifies(evidence, portfolio_state, reference_time):
    reality = qualify_internal_economic_reality((evidence,))
    assert reality.portfolio_state is portfolio_state
    assert reality.reference_time == reference_time
    assert reality.supporting_evidence == (evidence,)


def test_empty_portfolio_state_qualifies(reference_time):
    state = PortfolioState()
    evidence = InternalEconomicRealityEvidence(
        state, reference_time, InternalEconomicRealityProvenance("empty-ledger")
    )
    assert qualify_internal_economic_reality((evidence,)).portfolio_state is state


def test_multiple_provenances_and_equal_state_instances_are_compatible(
    portfolio_state, reference_time
):
    equal_state = PortfolioState(
        portfolio_state.positions, portfolio_state.monetary_balances
    )
    first = InternalEconomicRealityEvidence(
        portfolio_state, reference_time, InternalEconomicRealityProvenance("A")
    )
    second = InternalEconomicRealityEvidence(
        equal_state, reference_time, InternalEconomicRealityProvenance("B")
    )
    reality = qualify_internal_economic_reality((first, second))
    assert len(reality.supporting_evidence) == 2
    assert {item.provenance.value for item in reality.supporting_evidence} == {"A", "B"}


def test_incompatible_states_are_rejected(evidence, reference_time):
    other = InternalEconomicRealityEvidence(
        PortfolioState(), reference_time, InternalEconomicRealityProvenance("other")
    )
    with pytest.raises(InternalEconomicRealityQualificationDomainError):
        qualify_internal_economic_reality((evidence, other))


def test_incompatible_instants_are_rejected(evidence, portfolio_state):
    other = InternalEconomicRealityEvidence(
        portfolio_state,
        InternalEconomicRealityReferenceTime(
            datetime(2026, 8, 12, 17, tzinfo=timezone.utc)
        ),
        InternalEconomicRealityProvenance("other"),
    )
    with pytest.raises(InternalEconomicRealityQualificationDomainError):
        qualify_internal_economic_reality((evidence, other))


def test_ambiguous_reference_time_is_rejected():
    with pytest.raises(InternalEconomicRealityQualificationDomainError):
        InternalEconomicRealityReferenceTime(datetime(2026, 8, 12, 16))


def test_explicit_offsets_for_same_instant_have_same_temporal_meaning(portfolio_state):
    utc = InternalEconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
    )
    eastern = InternalEconomicRealityReferenceTime(
        datetime(2026, 8, 12, 12, tzinfo=timezone(timedelta(hours=-4)))
    )
    assert utc == eastern
    assert hash(utc) == hash(eastern)
    values = tuple(
        InternalEconomicRealityEvidence(
            portfolio_state, time, InternalEconomicRealityProvenance(source)
        )
        for time, source in ((utc, "A"), (eastern, "B"))
    )
    assert qualify_internal_economic_reality(values).reference_time == utc


def test_same_state_at_different_instants_produces_distinct_realities(portfolio_state):
    provenance = InternalEconomicRealityProvenance("ledger")
    times = (
        InternalEconomicRealityReferenceTime(
            datetime(2026, 8, 12, hour, tzinfo=timezone.utc)
        )
        for hour in (16, 17)
    )
    realities = tuple(
        qualify_internal_economic_reality(
            (InternalEconomicRealityEvidence(portfolio_state, time, provenance),)
        )
        for time in times
    )
    assert realities[0] != realities[1]
    assert realities[0].portfolio_state == realities[1].portfolio_state


def test_evidence_order_is_non_semantic_and_multiplicity_is_preserved(
    evidence, portfolio_state, reference_time
):
    second = InternalEconomicRealityEvidence(
        portfolio_state, reference_time, InternalEconomicRealityProvenance("second")
    )
    forward = qualify_internal_economic_reality((evidence, second, evidence))
    reverse = qualify_internal_economic_reality((evidence, second, evidence)[::-1])
    assert forward == reverse
    assert hash(forward) == hash(reverse)
    assert len(forward.supporting_evidence) == 3
    assert forward.supporting_evidence.count(evidence) == 2


def test_sources_and_published_reality_remain_immutable(evidence, portfolio_state):
    reality = qualify_internal_economic_reality((evidence,))
    original = (portfolio_state.positions, evidence.provenance, reality)
    with pytest.raises(FrozenInstanceError):
        evidence.provenance = InternalEconomicRealityProvenance("changed")
    qualify_internal_economic_reality((evidence,))
    assert (portfolio_state.positions, evidence.provenance, reality) == original


@pytest.mark.parametrize("invalid", [(), (object(),), None])
def test_missing_or_invalid_evidence_is_rejected(invalid):
    with pytest.raises(InternalEconomicRealityQualificationDomainError):
        qualify_internal_economic_reality(invalid)


def test_public_construction_cannot_bypass_evidence():
    with pytest.raises(InternalEconomicRealityQualificationDomainError):
        InternalEconomicReality()
    with pytest.raises(TypeError):
        InternalEconomicReality(portfolio_state=PortfolioState())
