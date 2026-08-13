from pathlib import Path

import quant_platform.economic_reality_verification as capability


ROOT = Path(__file__).parents[3]


def test_capability_is_separate_and_has_only_authorized_domain_dependencies():
    source = (
        ROOT
        / "src/quant_platform/economic_reality_verification/domain/verification.py"
    ).read_text()
    assert "quant_platform.internal_economic_reality" in source
    assert "quant_platform.external_economic_observation" in source
    assert "InstrumentReference" in source and "CurrencyReference" in source
    forbidden = ("Reconciliation", "Correction", "database", "broker", "network")
    assert not any(word in source for word in forbidden)
    assert hasattr(capability, "verify_economic_reality")


def test_preceding_capabilities_are_unchanged_by_verification_dependency():
    for relative in (
        "src/quant_platform/internal_economic_reality",
        "src/quant_platform/external_economic_observation",
        "src/quant_platform/portfolio",
    ):
        for path in (ROOT / relative).rglob("*.py"):
            assert "economic_reality_verification" not in path.read_text()
