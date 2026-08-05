"""Normative domain evidence for IT-031-001."""

from dataclasses import FrozenInstanceError

import pytest

from quant_platform.decision_model import DecisionProposal
from quant_platform.risk import (
    InconsistentRiskConditionsError,
    InvalidDecisionProposalError,
    InvalidEvaluationOutcomeError,
    InvalidRiskEvaluationBasisReferenceError,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)


def result(
    proposal: DecisionProposal,
    outcome: RiskEvaluationOutcome = RiskEvaluationOutcome.ACCEPTED,
    basis: str = "risk-contract-v1",
    conditions: tuple[str, ...] = (),
) -> RiskEvaluationResult:
    return RiskEvaluationResult(proposal, outcome, basis, conditions)


@pytest.mark.parametrize(
    ("outcome", "conditions"),
    [
        (RiskEvaluationOutcome.ACCEPTED, ()),
        (RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED, ("cap exposure",)),
        (RiskEvaluationOutcome.REJECTED, ()),
    ],
)
def test_constructs_each_authorized_outcome(
    proposal: DecisionProposal,
    outcome: RiskEvaluationOutcome,
    conditions: tuple[str, ...],
) -> None:
    created = result(proposal, outcome, conditions=conditions)

    assert created.outcome is outcome
    assert created.conditions == conditions


def test_requires_a_valid_decision_proposal() -> None:
    with pytest.raises(InvalidDecisionProposalError):
        RiskEvaluationResult(None, RiskEvaluationOutcome.ACCEPTED, "basis")  # type: ignore[arg-type]


@pytest.mark.parametrize("outcome", [None, "ACCEPTED"])
def test_rejects_absent_or_unauthorized_outcome(
    proposal: DecisionProposal, outcome: object
) -> None:
    with pytest.raises(InvalidEvaluationOutcomeError):
        RiskEvaluationResult(proposal, outcome, "basis")  # type: ignore[arg-type]


def test_conditionally_accepted_requires_conditions(proposal: DecisionProposal) -> None:
    with pytest.raises(InconsistentRiskConditionsError):
        result(proposal, RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED)


@pytest.mark.parametrize(
    "outcome", [RiskEvaluationOutcome.ACCEPTED, RiskEvaluationOutcome.REJECTED]
)
def test_only_conditional_acceptance_can_carry_conditions(
    proposal: DecisionProposal, outcome: RiskEvaluationOutcome
) -> None:
    with pytest.raises(InconsistentRiskConditionsError):
        result(proposal, outcome, conditions=("cap exposure",))


@pytest.mark.parametrize("basis", [None, "", "   ", 1])
def test_requires_valid_basis_reference(
    proposal: DecisionProposal, basis: object
) -> None:
    with pytest.raises(InvalidRiskEvaluationBasisReferenceError):
        result(proposal, basis=basis)  # type: ignore[arg-type]


def test_equivalent_instances_have_equal_identity_and_hash(
    proposal: DecisionProposal,
) -> None:
    first = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        conditions=("cap exposure", "require hedge"),
    )
    second = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        conditions=("require hedge", "cap exposure"),
    )

    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity
    assert first.conditions == ("cap exposure", "require hedge")


def test_identity_changes_with_proposal(
    proposal: DecisionProposal, other_proposal: DecisionProposal
) -> None:
    assert result(proposal) != result(other_proposal)


def test_identity_changes_with_outcome(proposal: DecisionProposal) -> None:
    assert result(proposal) != result(proposal, RiskEvaluationOutcome.REJECTED)


def test_identity_changes_with_basis(proposal: DecisionProposal) -> None:
    assert result(proposal) != result(proposal, basis="risk-contract-v2")


def test_identity_changes_with_conditions(proposal: DecisionProposal) -> None:
    first = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        conditions=("cap exposure",),
    )
    second = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        conditions=("require hedge",),
    )
    assert first != second


def test_is_immutable(proposal: DecisionProposal) -> None:
    created = result(proposal)
    with pytest.raises(FrozenInstanceError):
        created.outcome = RiskEvaluationOutcome.REJECTED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        created.conditions = ("changed",)  # type: ignore[misc]


def test_is_reproducible(proposal: DecisionProposal) -> None:
    assert result(proposal).semantic_identity == result(proposal).semantic_identity


def test_preserves_proposal_and_public_traceability(proposal: DecisionProposal) -> None:
    original_identity = proposal.semantic_identity
    original_evidence = proposal.evidence_references

    created = result(proposal)

    assert created.decision_proposal is proposal
    assert created.decision_proposal.semantic_identity == original_identity
    assert proposal.evidence_references == original_evidence
    assert created.basis_reference == "risk-contract-v1"


def test_unexpected_public_contract_error_is_not_translated() -> None:
    malformed = object.__new__(DecisionProposal)
    with pytest.raises(AttributeError):
        result(malformed)
