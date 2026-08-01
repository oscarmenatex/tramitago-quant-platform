import ast
from pathlib import Path

ROOT = Path(__file__).parents[3] / "src" / "quant_platform" / "strategy_evaluation"


def imports(name):
    tree = ast.parse((ROOT / name).read_text())
    return {
        (node.module or "").lower()
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }


def test_ar_001_comparator_port_does_not_import_registry_or_access():
    assert not any(
        "registry" in value or "access" in value
        for value in imports("domain/ports/strategy_evaluation_comparator.py")
    )


def test_ar_002_service_contains_no_concrete_quantitative_algorithm():
    tree = ast.parse(
        (ROOT / "application/strategy_evaluation_comparison_service.py").read_text()
    )
    service = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    assert {node.name for node in service.body if isinstance(node, ast.FunctionDef)} == {
        "__init__", "compare", "_validate_request", "_resolve_evaluation", "_validate_comparability", "_compare"
    }


def test_ar_003_registry_does_not_import_strategy_evaluation_access():
    assert not any(
        "strategy_evaluation_access" in value
        for value in imports("registry/strategy_evaluation_comparison_registry.py")
    )


def test_ar_004_new_modules_do_not_import_forbidden_domains():
    assert not any(
        any(
            part in {"knowledge", "data", "research", "risk", "portfolio", "execution"}
            for part in value.split(".")
        )
        for path in ROOT.rglob("*comparison*.py")
        for value in imports(path.relative_to(ROOT))
    )


def test_ar_005_it_027_001_public_contracts_are_not_redefined():
    assert (
        "class Strategy("
        not in (ROOT / "domain/entities/strategy_evaluation_comparison.py").read_text()
    )


def test_ar_006_it_027_002_public_contracts_are_not_redefined():
    assert (
        "class StrategyEvaluationAccess("
        not in (
            ROOT / "application/strategy_evaluation_comparison_service.py"
        ).read_text()
    )


def test_ar_007_no_external_dependency_was_added():
    assert all(
        value.startswith(
            ("quant_platform", "collections", "dataclasses", "typing", "__future__")
        )
        or not value
        for path in ROOT.rglob("*comparison*.py")
        for value in imports(path.relative_to(ROOT))
    )
