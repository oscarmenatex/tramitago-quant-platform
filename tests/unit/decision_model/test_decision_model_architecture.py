"""Architectural boundary evidence for IT-029-001."""

from pathlib import Path

import quant_platform.decision_model as decision_model
from quant_platform.decision_model import DecisionProposal


def test_decision_model_exposes_only_the_decision_proposal_asset() -> None:
    assert decision_model.__all__ == ["DecisionProposal"]


def test_domain_depends_only_on_the_public_resolution_contract() -> None:
    source = Path(DecisionProposal.__module__.replace(".", "/") + ".py")
    content = (Path("src") / source).read_text(encoding="utf-8")

    assert "strategy_evaluation.resolution import ResolutionResult" in content
    for prohibited_component in ("publication", "lifecycle", "registry", "risk", "portfolio", "execution"):
        assert f"strategy_evaluation.{prohibited_component}" not in content
