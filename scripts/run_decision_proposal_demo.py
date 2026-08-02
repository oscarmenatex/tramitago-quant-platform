"""Deterministic functional demonstration for IT-029-001."""

from quant_platform.decision_model import DecisionProposal
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class _PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def _resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", _PublicPublication(publication_id))
    return result


def main() -> None:
    evidence = (_resolution("resolved-public-evidence-a"),)
    proposal = DecisionProposal.from_resolutions("maintain current exposure", evidence)
    equivalent = DecisionProposal.from_resolutions("maintain current exposure", evidence)
    different_intent = DecisionProposal.from_resolutions("reduce exposure", evidence)
    different_evidence = DecisionProposal.from_resolutions(
        "maintain current exposure", (_resolution("resolved-public-evidence-b"),)
    )

    assert proposal == equivalent
    assert hash(proposal) == hash(equivalent)
    assert proposal != different_intent
    assert proposal != different_evidence
    assert proposal.evidence_references == ("resolved-public-evidence-a",)
    print(f"semantic_identity: {proposal.semantic_identity}")
    print(f"decision_intent: {proposal.decision_intent}")
    print(f"evidence_references: {proposal.evidence_references}")


if __name__ == "__main__":
    main()
