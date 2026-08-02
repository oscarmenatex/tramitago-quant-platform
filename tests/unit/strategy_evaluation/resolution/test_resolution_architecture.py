"""AR-T-001..AR-T-014 AST evidence for the Resolution boundary."""

import ast
from pathlib import Path


ROOT = Path("src/quant_platform/strategy_evaluation")
RESOLUTION = ROOT / "resolution"
SERVICE = RESOLUTION / "resolution_service.py"


def test_ar_t_001_to_016_uses_only_authorized_read_boundaries():
    source = "\n".join(path.read_text(encoding="utf-8") for path in RESOLUTION.glob("*.py"))
    modules = [node.module or "" for node in ast.walk(ast.parse(source)) if isinstance(node, ast.ImportFrom)]
    forbidden = ("registry", "domain.entities", "application", "research", "datetime", "threading", "cache")
    assert not any(token in module for module in modules for token in forbidden)
    assert "quant_platform.strategy_evaluation.publication.strategy_evaluation_publication_access" in modules
    assert "quant_platform.strategy_evaluation.publication.strategy_evaluation_comparison_publication_access" in modules
    assert "quant_platform.strategy_evaluation.lifecycle.access" in modules
    assert "datetime.now" not in source and ".register(" not in source
    assert not any("resolution" in path.read_text(encoding="utf-8") for path in (ROOT / "publication").glob("*.py"))
    assert not any("resolution" in path.read_text(encoding="utf-8") for path in (ROOT / "lifecycle").glob("*.py"))
    context = (RESOLUTION / "resolution_context.py").read_text(encoding="utf-8")
    assert "publication_id" not in context and "lifecycle_id" not in context
