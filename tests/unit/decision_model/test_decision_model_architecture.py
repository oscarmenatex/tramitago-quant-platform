"""Architectural boundary evidence for IT-029-001/002 v1.1."""

from pathlib import Path

import quant_platform.decision_model as decision_model
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)


def test_decision_model_exposes_the_complete_minimum_public_contract() -> None:
    assert decision_model.__all__ == [
        "DecisionProposal",
        "EconomicProposition",
        "ExposureOrientation",
    ]
    assert set(ExposureOrientation) == {
        ExposureOrientation.POSITIVE,
        ExposureOrientation.NEGATIVE,
        ExposureOrientation.FLAT,
    }


def test_domain_depends_only_on_authorized_public_contracts() -> None:
    source = Path(DecisionProposal.__module__.replace(".", "/") + ".py")
    content = (Path("src") / source).read_text(encoding="utf-8")

    assert "from quant_platform.core import InstrumentReference" in content
    assert "strategy_evaluation.resolution import ResolutionResult" in content
    for prohibited_component in (
        "publication",
        "lifecycle",
        "registry",
        "risk",
        "portfolio",
        "execution",
    ):
        assert f"strategy_evaluation.{prohibited_component}" not in content


def test_contracts_are_owned_by_decision_model_domain() -> None:
    assert DecisionProposal.__module__.startswith(
        "quant_platform.decision_model.domain"
    )
    assert EconomicProposition.__module__.startswith(
        "quant_platform.decision_model.domain"
    )
