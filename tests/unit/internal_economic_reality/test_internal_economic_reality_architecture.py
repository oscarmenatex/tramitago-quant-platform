import ast
from pathlib import Path

from quant_platform.internal_economic_reality import InternalEconomicRealityEvidence
from quant_platform.portfolio import PortfolioState


PACKAGE = Path("src/quant_platform/internal_economic_reality")


def test_capability_is_separate_and_reuses_portfolio_state_directly():
    annotations = InternalEconomicRealityEvidence.__annotations__
    assert annotations["portfolio_state"] is PortfolioState
    assert PACKAGE.is_dir()


def test_capability_has_no_forbidden_architectural_dependencies_or_duplicates():
    forbidden = {
        "external_economic_observation",
        "operational_materialization",
        "post_materialization_economic_consequence",
        "verification",
        "reconciliation",
        "database",
        "broker",
        "network",
    }
    source = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.rglob("*.py"))
    assert "class PortfolioState" not in source
    assert "class PortfolioPosition" not in source
    assert "class MonetaryBalance" not in source
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imported.update(
            name.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for name in node.names
        )
        assert not any(word in module for module in imported for word in forbidden)


def test_no_cross_capability_time_contract_was_added_to_core():
    core_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/core").rglob("*.py")
    )
    assert "EconomicRealityReferenceTime" not in core_source
