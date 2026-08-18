import ast
from pathlib import Path

from quant_platform.internal_economic_reality import InternalEconomicRealityEvidence
from quant_platform.portfolio import PortfolioState


PACKAGE = Path("src/quant_platform/internal_economic_reality")


def _package_source() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.rglob("*.py"))


def _imported_modules() -> set[str]:
    imported: set[str] = set()
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        imported.update(
            name.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for name in node.names
        )
    return imported


def test_qualification_is_owned_by_cap_007_reconciliation():
    import quant_platform.internal_economic_reality as qualification

    assert "CAP-007 Reconciliation" in qualification.__doc__
    assert PACKAGE.is_dir()


def test_qualification_reuses_portfolio_owned_state_directly():
    annotations = InternalEconomicRealityEvidence.__annotations__
    assert annotations["portfolio_state"] is PortfolioState
    source = _package_source()
    assert "class PortfolioState" not in source
    assert "class PortfolioPosition" not in source
    assert "class MonetaryBalance" not in source


def test_qualification_has_no_downstream_or_infrastructure_dependencies():
    forbidden = {
        "external_economic_observation",
        "operational_materialization",
        "post_materialization_economic_consequence",
        "economic_reality_verification",
        "verification",
        "database",
        "broker",
        "network",
    }
    imported = _imported_modules()
    assert not any(word in module for module in imported for word in forbidden)
    assert "quant_platform.execution" not in imported
    assert not any("reconciliation" in module for module in imported)


def test_qualification_does_not_assume_later_reconciliation_responsibilities():
    tree = ast.parse(_package_source())
    defined_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden_responsibilities = {
        "compare_economic_reality",
        "verify_economic_reality",
        "resolve_discrepancy",
        "correct_portfolio",
    }
    assert defined_names.isdisjoint(forbidden_responsibilities)


def test_no_cross_capability_time_contract_was_added_to_core():
    core_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/core").rglob("*.py")
    )
    assert "EconomicRealityReferenceTime" not in core_source
