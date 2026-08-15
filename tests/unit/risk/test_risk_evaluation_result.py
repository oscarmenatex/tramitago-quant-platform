"""Normative domain evidence for IT-031-001 v1.1."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from quant_platform.decision_model import DecisionProposal
from quant_platform.risk import (
    InconsistentRiskConstraintsError,
    InvalidDecisionProposalError,
    InvalidEvaluationOutcomeError,
    InvalidRiskConstraintError,
    InvalidRiskContextReferenceError,
    InvalidRiskEvaluationBasisReferenceError,
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)


def constraint(
    kind: RiskConstraintKind = RiskConstraintKind.MAX_EXPOSURE,
    limit: Decimal = Decimal("0.25"),
    unit: str = "NAV_RATIO",
) -> RiskConstraint:
    return RiskConstraint(kind, limit, unit)


def result(
    proposal: DecisionProposal,
    outcome: RiskEvaluationOutcome = RiskEvaluationOutcome.ACCEPTED,
    basis: str = "risk-contract-v1.1",
    constraints: tuple[RiskConstraint, ...] = (),
    context_references: tuple[str, ...] = (),
) -> RiskEvaluationResult:
    return RiskEvaluationResult(
        proposal, outcome, basis, constraints, context_references
    )


@pytest.mark.parametrize(
    ("outcome", "constraints"),
    [
        (RiskEvaluationOutcome.ACCEPTED, ()),
        (RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED, (constraint(),)),
        (RiskEvaluationOutcome.REJECTED, ()),
    ],
)
def test_constructs_each_authorized_outcome(
    proposal: DecisionProposal,
    outcome: RiskEvaluationOutcome,
    constraints: tuple[RiskConstraint, ...],
) -> None:
    created = result(proposal, outcome, constraints=constraints)

    assert created.outcome is outcome
    assert created.constraints == constraints


@pytest.mark.parametrize(
    ("kind", "limit", "unit"),
    [
        (RiskConstraintKind.MAX_CAPITAL, Decimal("100000"), "USD"),
        (RiskConstraintKind.MAX_EXPOSURE, Decimal("0.30"), "NAV_RATIO"),
        (RiskConstraintKind.MAX_SIZE, Decimal("250"), "SHARES"),
        (RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("50"), "SHARES"),
    ],
)
def test_represents_structured_quantitative_limits(
    kind: RiskConstraintKind, limit: Decimal, unit: str
) -> None:
    created = constraint(kind, limit, unit)

    assert created.kind is kind
    assert created.limit == limit
    assert created.unit == unit


@pytest.mark.parametrize(
    ("kind", "limit", "unit"),
    [
        ("MAX_CAPITAL", Decimal("1"), "USD"),
        (RiskConstraintKind.MAX_CAPITAL, 1, "USD"),
        (RiskConstraintKind.MAX_CAPITAL, Decimal("NaN"), "USD"),
        (RiskConstraintKind.MAX_CAPITAL, Decimal("Infinity"), "USD"),
        (RiskConstraintKind.MAX_CAPITAL, Decimal("1"), ""),
        (RiskConstraintKind.MAX_CAPITAL, Decimal("1"), "   "),
    ],
)
def test_rejects_invalid_constraints(kind: object, limit: object, unit: object) -> None:
    with pytest.raises(InvalidRiskConstraintError):
        RiskConstraint(kind, limit, unit)  # type: ignore[arg-type]


def test_requires_a_valid_decision_proposal() -> None:
    with pytest.raises(InvalidDecisionProposalError):
        RiskEvaluationResult(None, RiskEvaluationOutcome.ACCEPTED, "basis")  # type: ignore[arg-type]


@pytest.mark.parametrize("outcome", [None, "ACCEPTED"])
def test_rejects_absent_or_unauthorized_outcome(
    proposal: DecisionProposal, outcome: object
) -> None:
    with pytest.raises(InvalidEvaluationOutcomeError):
        RiskEvaluationResult(proposal, outcome, "basis")  # type: ignore[arg-type]


def test_conditionally_accepted_requires_constraints(
    proposal: DecisionProposal,
) -> None:
    with pytest.raises(InconsistentRiskConstraintsError):
        result(proposal, RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED)


@pytest.mark.parametrize(
    "outcome", [RiskEvaluationOutcome.ACCEPTED, RiskEvaluationOutcome.REJECTED]
)
def test_only_conditional_acceptance_can_carry_constraints(
    proposal: DecisionProposal, outcome: RiskEvaluationOutcome
) -> None:
    with pytest.raises(InconsistentRiskConstraintsError):
        result(proposal, outcome, constraints=(constraint(),))


def test_rejects_non_constraint_collection_members(
    proposal: DecisionProposal,
) -> None:
    with pytest.raises(InvalidRiskConstraintError):
        result(
            proposal,
            RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
            constraints=("cap exposure",),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("basis", [None, "", "   ", 1])
def test_requires_valid_basis_reference(
    proposal: DecisionProposal, basis: object
) -> None:
    with pytest.raises(InvalidRiskEvaluationBasisReferenceError):
        result(proposal, basis=basis)  # type: ignore[arg-type]


@pytest.mark.parametrize("reference", [None, "", "   ", 1])
def test_rejects_invalid_context_reference(
    proposal: DecisionProposal, reference: object
) -> None:
    with pytest.raises(InvalidRiskContextReferenceError):
        result(proposal, context_references=(reference,))  # type: ignore[arg-type]


def test_order_does_not_change_semantics(proposal: DecisionProposal) -> None:
    capital = constraint(RiskConstraintKind.MAX_CAPITAL, Decimal("100000"), "USD")
    sizing = constraint(RiskConstraintKind.MAX_SIZE, Decimal("250"), "SHARES")
    first = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(capital, sizing),
        context_references=("exposure-state:42", "market-state:17"),
    )
    second = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(sizing, capital),
        context_references=("market-state:17", "exposure-state:42"),
    )

    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity
    assert first.constraints == (capital, sizing)
    assert first.context_references == ("exposure-state:42", "market-state:17")


def test_each_contract_component_participates_in_identity(
    proposal: DecisionProposal, other_proposal: DecisionProposal
) -> None:
    accepted = result(proposal)
    assert accepted != result(other_proposal)
    assert accepted != result(proposal, RiskEvaluationOutcome.REJECTED)
    assert accepted != result(proposal, basis="risk-contract-v2")
    assert accepted != result(proposal, context_references=("context:1",))

    exposure = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(constraint(),),
    )
    capital = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(constraint(RiskConstraintKind.MAX_CAPITAL),),
    )
    assert exposure != capital


def test_result_and_constraint_are_immutable(proposal: DecisionProposal) -> None:
    limit = constraint()
    created = result(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(limit,),
    )
    with pytest.raises(FrozenInstanceError):
        created.outcome = RiskEvaluationOutcome.REJECTED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        created.constraints = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        limit.limit = Decimal("1")  # type: ignore[misc]


def test_is_reproducible(proposal: DecisionProposal) -> None:
    assert result(proposal).semantic_identity == result(proposal).semantic_identity


def test_preserves_proposal_basis_and_public_context(
    proposal: DecisionProposal,
) -> None:
    original_identity = proposal.semantic_identity
    original_evidence = proposal.evidence_references

    created = result(proposal, context_references=("exposure-state:42",))

    assert created.decision_proposal is proposal
    assert created.decision_proposal.semantic_identity == original_identity
    assert proposal.evidence_references == original_evidence
    assert created.basis_reference == "risk-contract-v1.1"
    assert created.context_references == ("exposure-state:42",)


def test_unexpected_public_contract_error_is_not_translated() -> None:
    malformed = object.__new__(DecisionProposal)
    with pytest.raises(AttributeError):
        result(malformed)
