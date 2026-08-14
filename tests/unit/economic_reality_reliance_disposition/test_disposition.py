from dataclasses import FrozenInstanceError

import pytest

from quant_platform.economic_reality_reliance_disposition import (
    EconomicRealityRelianceAuthority,
    EconomicRealityRelianceDisposition,
    EconomicRealityRelianceDispositionDomainError,
    EconomicRealityRelianceOutcome as Outcome,
    dispose_economic_reality_reliance,
)
from quant_platform.post_verification_qualification import (
    PostVerificationQualificationCondition as Condition,
)


@pytest.mark.parametrize("condition", tuple(Condition))
def test_every_upstream_condition_is_consumed_without_reinterpretation(
    qualify, condition
):
    qualification = qualify(condition.value)
    authority = EconomicRealityRelianceAuthority(
        {condition: Outcome.RELIANCE_PERMITTED}
    )

    disposition = dispose_economic_reality_reliance(qualification, authority)

    assert qualification.condition is condition
    assert disposition.outcome is Outcome.RELIANCE_PERMITTED


def test_explicit_authorities_can_dispose_same_condition_differently(qualify):
    qualification = qualify("CORROBORATED")
    permitting = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PERMITTED}
    )
    prohibiting = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PROHIBITED}
    )

    first = dispose_economic_reality_reliance(qualification, permitting)
    second = dispose_economic_reality_reliance(qualification, prohibiting)

    assert first.outcome is Outcome.RELIANCE_PERMITTED
    assert second.outcome is Outcome.RELIANCE_PROHIBITED
    assert first.qualification is second.qualification is qualification
    assert first.authority is permitting
    assert second.authority is prohibiting
    assert first.outcome is Outcome.RELIANCE_PERMITTED


def test_insufficient_authority_is_a_domain_error_without_third_outcome(qualify):
    qualification = qualify("INSUFFICIENT_EVIDENCE")
    authority = EconomicRealityRelianceAuthority({})

    with pytest.raises(EconomicRealityRelianceDispositionDomainError):
        dispose_economic_reality_reliance(qualification, authority)

    assert {outcome.name for outcome in Outcome} == {
        "RELIANCE_PERMITTED",
        "RELIANCE_PROHIBITED",
    }


def test_partial_authority_disposes_only_a_covered_qualification(qualify):
    covered = qualify("CORROBORATED")
    uncovered = qualify("DIVERGENT")
    authority = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PERMITTED}
    )

    disposition = dispose_economic_reality_reliance(covered, authority)

    assert disposition.qualification is covered
    assert disposition.authority is authority
    assert disposition.outcome is Outcome.RELIANCE_PERMITTED
    with pytest.raises(EconomicRealityRelianceDispositionDomainError):
        dispose_economic_reality_reliance(uncovered, authority)
    assert {outcome.name for outcome in Outcome} == {
        "RELIANCE_PERMITTED",
        "RELIANCE_PROHIBITED",
    }


def test_sources_and_published_disposition_are_immutable(qualify):
    qualification = qualify("DIVERGENT")
    authority = EconomicRealityRelianceAuthority(
        {Condition.DIVERGENT: Outcome.RELIANCE_PROHIBITED}
    )
    disposition = dispose_economic_reality_reliance(qualification, authority)

    assert disposition.qualification is qualification
    assert disposition.authority is authority
    with pytest.raises((FrozenInstanceError, AttributeError)):
        disposition.outcome = Outcome.RELIANCE_PERMITTED
    with pytest.raises((FrozenInstanceError, AttributeError)):
        qualification.condition = Condition.CORROBORATED
    with pytest.raises((FrozenInstanceError, AttributeError)):
        authority.rules = frozenset()


def test_contractually_equivalent_authorities_preserve_meaning(qualify):
    qualification = qualify("CORROBORATED")
    left = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PERMITTED}
    )
    right = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PERMITTED}
    )

    assert left == right
    assert dispose_economic_reality_reliance(qualification, left).outcome is (
        dispose_economic_reality_reliance(qualification, right).outcome
    )


def test_invalid_inputs_and_public_construction_cannot_bypass_derivation(qualify):
    authority = EconomicRealityRelianceAuthority(
        {Condition.CORROBORATED: Outcome.RELIANCE_PROHIBITED}
    )
    with pytest.raises(EconomicRealityRelianceDispositionDomainError):
        dispose_economic_reality_reliance(object(), authority)
    with pytest.raises(EconomicRealityRelianceDispositionDomainError):
        dispose_economic_reality_reliance(qualify("CORROBORATED"), object())
    with pytest.raises(EconomicRealityRelianceDispositionDomainError):
        EconomicRealityRelianceDisposition()
    with pytest.raises(TypeError):
        EconomicRealityRelianceDisposition(
            qualification=qualify("CORROBORATED"),
            authority=authority,
            outcome=Outcome.RELIANCE_PERMITTED,
        )
