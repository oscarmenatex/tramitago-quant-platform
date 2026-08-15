"""Deterministic functional demonstration for IT-029-001/002 v1.1."""

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class _PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def _resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", _PublicPublication(publication_id))
    return result


def main() -> None:
    instrument = InstrumentReference("FIGI", "BBG000B9XRY4")
    positive = EconomicProposition(instrument, ExposureOrientation.POSITIVE)
    negative = EconomicProposition(instrument, ExposureOrientation.NEGATIVE)
    evidence = (_resolution("resolved-public-evidence-a"),)

    proposal = DecisionProposal.from_resolutions(positive, evidence)
    equivalent = DecisionProposal.from_resolutions(positive, evidence)
    different_orientation = DecisionProposal.from_resolutions(negative, evidence)

    assert proposal.economic_proposition is positive
    assert proposal.economic_proposition.instrument is instrument
    assert proposal.evidence_references == ("resolved-public-evidence-a",)
    assert proposal == equivalent
    assert hash(proposal) == hash(equivalent)
    assert proposal.semantic_identity == equivalent.semantic_identity
    assert proposal != different_orientation

    print(f"economic_proposition: {proposal.economic_proposition}")
    print(f"evidence_references: {proposal.evidence_references}")
    print(f"semantic_identity: {proposal.semantic_identity}")
    print("construction_received_explicit_proposition: True")


if __name__ == "__main__":
    main()
