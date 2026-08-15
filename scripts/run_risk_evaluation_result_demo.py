"""Deterministic functional demonstration for IT-031-001 v1.1."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

from quant_platform.decision_model import DecisionProposal
from quant_platform.risk import (
    InconsistentRiskConstraintsError,
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class _PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def _resolution(publication_id: str) -> ResolutionResult:
    resolved = object.__new__(ResolutionResult)
    object.__setattr__(resolved, "publication", _PublicPublication(publication_id))
    return resolved


def main() -> None:
    proposal = DecisionProposal.from_resolutions(
        "maintain current exposure", (_resolution("resolved-evidence-a"),)
    )
    original_identity = proposal.semantic_identity
    context = ("exposure-state:42", "market-state:17")
    exposure_limit = RiskConstraint(
        RiskConstraintKind.MAX_EXPOSURE, Decimal("0.25"), "NAV_RATIO"
    )

    accepted = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.ACCEPTED,
        "risk-contract-v1.1",
        context_references=context,
    )
    equivalent = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.ACCEPTED,
        "risk-contract-v1.1",
        context_references=tuple(reversed(context)),
    )
    conditional = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-contract-v1.1",
        (exposure_limit,),
        context,
    )
    rejected = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.REJECTED,
        "risk-contract-v1.1",
        context_references=context,
    )

    assert accepted == equivalent
    assert accepted.semantic_identity == equivalent.semantic_identity
    assert accepted != conditional != rejected
    assert proposal.semantic_identity == original_identity
    assert all(
        item.decision_proposal is proposal for item in (accepted, conditional, rejected)
    )
    assert conditional.constraints == (exposure_limit,)
    assert conditional.basis_reference == "risk-contract-v1.1"
    assert conditional.context_references == tuple(sorted(context))

    try:
        accepted.constraints = (exposure_limit,)  # type: ignore[misc]
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("RiskEvaluationResult must be immutable")

    try:
        RiskEvaluationResult(
            proposal,
            RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
            "risk-contract-v1.1",
        )
    except InconsistentRiskConstraintsError as error:
        print(f"structural_error: {type(error).__name__}")
    else:
        raise AssertionError("Missing conditional acceptance error")

    for item in (accepted, conditional, rejected):
        print(f"{item.outcome.value}: {item.semantic_identity}")
    print(f"constraint: {exposure_limit}")
    print(f"basis_reference: {conditional.basis_reference}")
    print(f"context_references: {conditional.context_references}")
    print(f"proposal_preserved: {proposal.semantic_identity == original_identity}")
    print("identity_reproducible: True")


if __name__ == "__main__":
    main()
