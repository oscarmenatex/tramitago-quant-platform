import ast
from pathlib import Path


ROOT = Path("src/quant_platform/strategy_evaluation")
PUBLICATION = ROOT / "publication"
SERVICES = (
    ROOT / "application" / "strategy_evaluation_publication_service.py",
    ROOT / "application" / "strategy_evaluation_comparison_publication_service.py",
)


def imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]


def test_ar_001_services_depend_on_authorized_boundaries_not_source_entities():
    for path in SERVICES:
        values = imports(path)
        assert "quant_platform.strategy_evaluation.domain.entities" not in values
        assert "quant_platform.strategy_evaluation.registry" in values
        assert "quant_platform.strategy_evaluation.publication" in values


def test_ar_002_registries_do_not_import_source_accesses():
    for path in PUBLICATION.glob("*publication_registry.py"):
        assert not any(
            "strategy_evaluation.registry" in value for value in imports(path)
        )


def test_ar_003_accesses_do_not_import_services_or_source_accesses():
    for path in PUBLICATION.glob("*publication_access.py"):
        values = imports(path)
        assert not any(
            "application" in value or "strategy_evaluation.registry" in value
            for value in values
        )


def test_ar_004_public_models_do_not_reference_internal_entities():
    for path in PUBLICATION.glob("published_*.py"):
        assert "domain.entities" not in path.read_text(encoding="utf-8")


def test_ar_005_has_no_prohibited_domain_imports():
    prohibited = (
        "knowledge",
        "data",
        "dataset",
        "research",
        "risk",
        "portfolio",
        "execution",
    )
    for path in (*PUBLICATION.glob("*.py"), *SERVICES):
        assert not any(
            any(term in value.lower().split(".") for term in prohibited)
            for value in imports(path)
        )


def test_ar_006_strategy_evaluation_contract_is_not_redefined():
    definitions = [
        path
        for path in ROOT.rglob("*.py")
        if "class StrategyEvaluation:" in path.read_text(encoding="utf-8")
    ]
    assert definitions == [ROOT / "domain" / "entities" / "strategy_evaluation.py"]


def test_ar_007_evaluation_access_contract_is_not_redefined():
    definitions = [
        path
        for path in ROOT.rglob("*.py")
        if "class StrategyEvaluationAccess:" in path.read_text(encoding="utf-8")
    ]
    assert definitions == [ROOT / "registry" / "strategy_evaluation_access.py"]


def test_ar_008_comparison_contract_is_not_redefined():
    definitions = [
        path
        for path in ROOT.rglob("*.py")
        if "class StrategyEvaluationComparison:" in path.read_text(encoding="utf-8")
    ]
    assert definitions == [
        ROOT / "domain" / "entities" / "strategy_evaluation_comparison.py"
    ]


def test_ar_009_has_explicit_models_not_a_generic_publication_container():
    content = "\n".join(
        path.read_text(encoding="utf-8") for path in PUBLICATION.glob("*.py")
    )
    assert "class PublishedStrategyEvaluation:" in content
    assert "class PublishedStrategyEvaluationComparison:" in content
    assert "GenericPublication" not in content


def test_ar_010_new_modules_use_only_standard_library_or_quant_platform_imports():
    for path in (*PUBLICATION.glob("*.py"), *SERVICES):
        assert all(
            value.startswith("quant_platform")
            or value.split(".", 1)[0] in {"collections", "dataclasses", "typing"}
            or not value
            for value in imports(path)
        )
