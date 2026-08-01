"""AR-001..AR-012 AST evidence for the Lifecycle architectural boundary."""

import ast
from pathlib import Path


ROOT = Path("src/quant_platform/strategy_evaluation")
LIFECYCLE = ROOT / "lifecycle"
SERVICE = ROOT / "application" / "publication_lifecycle_service.py"


def imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]


def test_lar_001_to_005_dependency_direction_and_authorized_accesses():
    assert "quant_platform.strategy_evaluation.domain.entities" not in imports(SERVICE)
    assert "quant_platform.strategy_evaluation.registry" not in imports(SERVICE)
    assert "quant_platform.strategy_evaluation.publication" in imports(SERVICE)
    for path in (ROOT / "publication").glob("*.py"):
        assert "lifecycle" not in path.read_text(encoding="utf-8")
    for path in LIFECYCLE.glob("*.py"):
        assert "application" not in imports(path)


def test_lar_006_to_012_standard_library_no_clock_and_no_write_boundaries():
    source = SERVICE.read_text(encoding="utf-8")
    assert "datetime.now" not in source and "datetime.utcnow" not in source
    for path in (*LIFECYCLE.glob("*.py"), SERVICE):
        assert all(value.startswith("quant_platform") or value.split(".", 1)[0] in {"dataclasses", "datetime", "enum", "typing"} or not value for value in imports(path))
    registry = (LIFECYCLE / "registries.py").read_text(encoding="utf-8")
    access = (LIFECYCLE / "access.py").read_text(encoding="utf-8")
    assert "PublicationLifecycleStatus" not in registry
    assert ".append(" not in access and ".register(" not in access
    content = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.rglob("*.py"))
    assert content.count("class PublishedStrategyEvaluation:") == 1
    assert content.count("class PublishedStrategyEvaluationComparison:") == 1
