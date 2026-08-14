from dataclasses import FrozenInstanceError

import pytest

from quant_platform.economic_reality_verification import EconomicRealityDimension as D
from quant_platform.post_verification_qualification import (
    PostVerificationQualification,
    PostVerificationQualificationCondition as C,
    PostVerificationQualificationDomainError,
    RequiredCorroborationRequirement as Requirement,
    RequiredCorroborationScope as Scope,
    qualify_post_verification,
)


def req(dimension, identity):
    return Requirement(dimension, identity)


def qualify(verification, *requirements):
    return qualify_post_verification(verification, Scope(requirements))


def test_all_required_agreement_is_corroborated(make_verification, identities):
    aapl, _, _, usd = identities
    v = make_verification(internal_positions=((aapl, 10),), external_positions=((aapl, 10),),
                          internal_money=((usd, 5),), external_money=((usd, 5),))
    assert qualify(v, req(D.POSITION, aapl), req(D.MONETARY_BALANCE, usd)).condition is C.CORROBORATED


def test_required_discrepancy_is_divergent(make_verification, identities):
    aapl, _, _, _ = identities
    v = make_verification(internal_positions=((aapl, 10),), external_positions=((aapl, 11),))
    assert qualify(v, req(D.POSITION, aapl)).condition is C.DIVERGENT


def test_not_comparable_is_insufficient(make_verification, identities):
    aapl, msft, _, _ = identities
    v = make_verification(internal_positions=((msft, 5),), external_positions=((aapl, 1),))
    assert qualify(v, req(D.POSITION, msft)).condition is C.INSUFFICIENT_EVIDENCE


def test_missing_result_is_insufficient_without_synthetic_result(make_verification, identities):
    aapl, _, tsla, _ = identities
    v = make_verification(internal_positions=((aapl, 1),), external_positions=((aapl, 1),))
    before = v.position_results
    assert qualify(v, req(D.POSITION, tsla)).condition is C.INSUFFICIENT_EVIDENCE
    assert v.position_results is before and all(x.identity != tsla for x in before)


@pytest.mark.parametrize("missing", [False, True])
def test_discrepancy_precedes_insufficient_evidence(make_verification, identities, missing):
    aapl, msft, tsla, _ = identities
    v = make_verification(internal_positions=((aapl, 1), (msft, 1)),
                          external_positions=((aapl, 2),), covered_positions=(aapl,))
    other = tsla if missing else msft
    assert qualify(v, req(D.POSITION, aapl), req(D.POSITION, other)).condition is C.DIVERGENT


def test_results_outside_scope_are_ignored(make_verification, identities):
    aapl, msft, _, _ = identities
    v = make_verification(internal_positions=((aapl, 1), (msft, 1)),
                          external_positions=((aapl, 1), (msft, 2)))
    assert qualify(v, req(D.POSITION, aapl)).condition is C.CORROBORATED


def test_empty_verification_is_valid_but_insufficient(make_verification, identities):
    aapl, _, _, _ = identities
    v = make_verification()
    assert qualify(v, req(D.POSITION, aapl)).condition is C.INSUFFICIENT_EVIDENCE


def test_scope_is_nonempty_order_independent_and_deduplicated(identities):
    aapl, _, _, usd = identities
    position, money = req(D.POSITION, aapl), req(D.MONETARY_BALANCE, usd)
    assert Scope((position, money, position)) == Scope((money, position))
    assert len(Scope((position, position)).requirements) == 1
    with pytest.raises(PostVerificationQualificationDomainError):
        Scope(())


def test_requirement_order_has_no_public_qualification_meaning(
    make_verification, identities
):
    aapl, _, _, usd = identities
    verification = make_verification(
        internal_positions=((aapl, 10),),
        external_positions=((aapl, 10),),
        internal_money=((usd, 5),),
        external_money=((usd, 5),),
    )
    position = req(D.POSITION, aapl)
    monetary = req(D.MONETARY_BALANCE, usd)
    first_scope = Scope((position, monetary))
    reversed_scope = Scope((monetary, position))

    first_qualification = qualify_post_verification(verification, first_scope)
    reversed_qualification = qualify_post_verification(
        verification, reversed_scope
    )

    assert first_scope == reversed_scope
    assert first_qualification.condition == reversed_qualification.condition
    assert first_qualification == reversed_qualification


def test_position_and_monetary_require_existing_identity_types(identities):
    aapl, _, _, usd = identities
    assert req(D.POSITION, aapl).identity is aapl
    assert req(D.MONETARY_BALANCE, usd).identity is usd
    with pytest.raises(PostVerificationQualificationDomainError):
        req(D.POSITION, usd)
    with pytest.raises(PostVerificationQualificationDomainError):
        req(D.MONETARY_BALANCE, aapl)


def test_provenance_and_immutability(make_verification, identities):
    aapl, _, _, _ = identities
    v = make_verification(internal_positions=((aapl, 1),), external_positions=((aapl, 1),))
    scope = Scope((req(D.POSITION, aapl),))
    q = qualify_post_verification(v, scope)
    assert q.verification is v and q.required_scope is scope
    with pytest.raises(FrozenInstanceError):
        q.condition = C.DIVERGENT
    with pytest.raises(FrozenInstanceError):
        scope.requirements = frozenset()
    later = qualify_post_verification(v, scope)
    assert q.condition is C.CORROBORATED and later is not q


def test_public_construction_and_invalid_inputs_cannot_bypass_invariants(make_verification):
    with pytest.raises(PostVerificationQualificationDomainError):
        PostVerificationQualification()
    with pytest.raises(PostVerificationQualificationDomainError):
        qualify_post_verification(object(), object())
    with pytest.raises(PostVerificationQualificationDomainError):
        qualify_post_verification(make_verification(), object())
