"""Architectural boundary evidence for IT-031-001."""

from pathlib import Path

import quant_platform.risk as risk
from quant_platform.risk import RiskConstraint, RiskEvaluationResult


def test_risk_exports_only_the_minimum_explicit_public_contract() -> None:
    assert risk.__all__ == [
        "InconsistentRiskConstraintsError",
        "InvalidDecisionProposalError",
        "InvalidEvaluationOutcomeError",
        "InvalidRiskConstraintError",
        "InvalidRiskContextReferenceError",
        "InvalidRiskEvaluationBasisReferenceError",
        "RiskConstraint",
        "RiskConstraintKind",
        "RiskEvaluationOutcome",
        "RiskEvaluationResult",
        "RiskEvaluationResultError",
    ]


def test_domain_depends_only_on_authorized_public_decision_contract() -> None:
    source = Path("src/quant_platform/risk/domain/risk_evaluation_result.py")
    content = source.read_text(encoding="utf-8")

    assert "from quant_platform.decision_model import DecisionProposal" in content
    assert "decision_model.domain" not in content
    for prohibited in (
        "strategy_evaluation",
        "portfolio",
        "execution",
        "infrastructure",
        "persistence",
        "registry",
        "service",
    ):
        assert f"quant_platform.{prohibited}" not in content


def test_increment_does_not_modify_decision_model() -> None:
    assert RiskEvaluationResult.__module__.startswith("quant_platform.risk.domain")
    assert RiskConstraint.__module__.startswith("quant_platform.risk.domain")
    assert not Path("src/quant_platform/decision_model").joinpath("risk.py").exists()
