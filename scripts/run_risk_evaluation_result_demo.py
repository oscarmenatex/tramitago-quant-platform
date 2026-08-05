"""Deterministic functional demonstration for IT-031-001."""

from quant_platform.decision_model import DecisionProposal
from quant_platform.risk import (
    InconsistentRiskConditionsError,
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
    accepted = RiskEvaluationResult(
        proposal, RiskEvaluationOutcome.ACCEPTED, "risk-contract-v1"
    )
    equivalent = RiskEvaluationResult(
        proposal, RiskEvaluationOutcome.ACCEPTED, "risk-contract-v1"
    )
    conditional = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-contract-v1",
        ("cap exposure", "require hedge"),
    )
    rejected = RiskEvaluationResult(
        proposal, RiskEvaluationOutcome.REJECTED, "risk-contract-v1"
    )
    different_basis = RiskEvaluationResult(
        proposal, RiskEvaluationOutcome.ACCEPTED, "risk-contract-v2"
    )
    different_conditions = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-contract-v1",
        ("require hedge",),
    )

    assert accepted == equivalent
    assert accepted.semantic_identity == equivalent.semantic_identity
    assert accepted != rejected
    assert accepted != different_basis
    assert conditional != different_conditions
    assert proposal.semantic_identity == original_identity
    assert accepted.decision_proposal is proposal
    try:
        RiskEvaluationResult(
            proposal, RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED, "risk-contract-v1"
        )
    except InconsistentRiskConditionsError as error:
        print(f"structural_error: {type(error).__name__}")
    else:
        raise AssertionError("Missing conditional acceptance error")

    for item in (accepted, conditional, rejected):
        print(f"{item.outcome.value}: {item.semantic_identity}")
    print(f"conditions: {conditional.conditions}")
    print(f"proposal_preserved: {proposal.semantic_identity == original_identity}")


if __name__ == "__main__":
    main()
