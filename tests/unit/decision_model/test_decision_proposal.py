"""Normative evidence for IT-029-001 Decision Proposal."""

from dataclasses import FrozenInstanceError

import pytest

from quant_platform.decision_model import DecisionProposal
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    """Minimal public projection fixture; no Strategy Evaluation internals."""

    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def resolution(publication_id: str) -> ResolutionResult:
    # ResolutionResult validates concrete public projections in production.  This
    # fixture models its stable public reference without importing those internals.
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", PublicPublication(publication_id))
    return result


def proposal(*evidence_ids: str, intent: str = "enter defensive posture") -> DecisionProposal:
    return DecisionProposal.from_resolutions(intent, tuple(resolution(item) for item in evidence_ids))


def test_equivalent_public_evidence_and_intent_have_semantic_identity() -> None:
    first = proposal("resolution-b", "resolution-a")
    second = proposal("resolution-a", "resolution-b")

    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity
    assert first.evidence_references == ("resolution-a", "resolution-b")


def test_changing_any_semantic_identity_element_creates_a_different_proposal() -> None:
    baseline = proposal("resolution-a")

    assert baseline != proposal("resolution-a", intent="reduce exposure")
    assert baseline != proposal("resolution-b")


def test_proposal_is_immutable_and_exposes_public_traceability() -> None:
    created = proposal("resolution-a")

    with pytest.raises(FrozenInstanceError):
        created.decision_intent = "altered"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        created.evidence_references = ()  # type: ignore[misc]
    assert created.evidence_references == ("resolution-a",)


@pytest.mark.parametrize(
    ("intent", "evidence", "error"),
    [
        ("", ("resolution-a",), ValueError),
        ("valid", (), ValueError),
        ("valid", ("resolution-a", "resolution-a"), ValueError),
    ],
)
def test_proposal_requires_one_intent_and_coherent_unique_public_evidence(
    intent: str, evidence: tuple[str, ...], error: type[Exception]
) -> None:
    with pytest.raises(error):
        proposal(*evidence, intent=intent)


def test_proposal_rejects_evidence_outside_the_public_resolution_contract() -> None:
    with pytest.raises(TypeError):
        DecisionProposal.from_resolutions("valid", (object(),))  # type: ignore[arg-type]
