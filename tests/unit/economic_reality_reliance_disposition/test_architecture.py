from pathlib import Path

import quant_platform.economic_reality_reliance_disposition as capability
from quant_platform.post_verification_qualification import PostVerificationQualification


ROOT = Path(__file__).parents[3]
PACKAGE = ROOT / "src/quant_platform/economic_reality_reliance_disposition"


def test_separate_capability_depends_only_on_public_qualification_contracts():
    source = "\n".join(path.read_text() for path in PACKAGE.rglob("*.py"))
    assert "quant_platform.post_verification_qualification import" in source
    forbidden = (
        "quant_platform.risk",
        "reconciliation",
        "correction",
        "operations",
        "execution",
        "provider",
        "network",
        "database",
        "PortfolioState",
        "EconomicRealityVerification",
        "RequiredCorroborationScope",
        "InternalEconomicReality",
        "ExternallyObservedEconomicReality",
    )
    assert not any(value in source for value in forbidden)
    assert capability.EconomicRealityRelianceDisposition.__annotations__[
        "qualification"
    ] is (PostVerificationQualification)


def test_no_reverse_dependency_or_local_qualification_wrapper():
    upstream = ROOT / "src/quant_platform/post_verification_qualification"
    assert all(
        "economic_reality_reliance_disposition" not in path.read_text()
        for path in upstream.rglob("*.py")
    )
    source = "\n".join(path.read_text() for path in PACKAGE.rglob("*.py"))
    assert "class PostVerificationQualification" not in source
    assert "Scope" not in source
    assert not any(
        term in source
        for term in ("reference_time", "disposed_at", "evaluated_at", "created_at")
    )
