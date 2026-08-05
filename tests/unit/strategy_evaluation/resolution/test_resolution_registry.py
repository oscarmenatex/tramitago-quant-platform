"""Evidence that Resolution introduces no registry or persistence mechanism."""

from pathlib import Path


def test_resolution_registry_is_absent_and_only_public_boundaries_exist():
    root = Path("src/quant_platform/strategy_evaluation/resolution")
    assert not list(root.glob("*registry*.py"))
