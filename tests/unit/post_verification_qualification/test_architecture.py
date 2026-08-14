from pathlib import Path

import quant_platform.post_verification_qualification as capability
from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import EconomicRealityDimension


ROOT = Path(__file__).parents[3]


def test_separate_capability_uses_only_public_upstream_contracts():
    source = (ROOT / "src/quant_platform/post_verification_qualification/domain/qualification.py").read_text()
    assert "quant_platform.economic_reality_verification import" in source
    assert "EconomicRealityDimension" in source
    assert "InstrumentReference" in source and "CurrencyReference" in source
    forbidden = ("quant_platform.risk", "operations", "reconciliation", "provider", "network", "database", "PortfolioState")
    assert not any(word in source for word in forbidden)
    assert capability.RequiredCorroborationRequirement.__annotations__["dimension"] is EconomicRealityDimension
    assert InstrumentReference is not CurrencyReference


def test_verification_has_no_reverse_dependency_or_local_outcome_copy():
    for path in (ROOT / "src/quant_platform/economic_reality_verification").rglob("*.py"):
        assert "post_verification_qualification" not in path.read_text()
    source = (ROOT / "src/quant_platform/post_verification_qualification/domain/qualification.py").read_text()
    assert "class EconomicRealityVerificationOutcome" not in source
