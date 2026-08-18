from pathlib import Path

import quant_platform.economic_reality_verification as capability


ROOT = Path(__file__).parents[3]
PACKAGE = ROOT / "src/quant_platform/economic_reality_verification"
VERIFICATION_SOURCE = PACKAGE / "domain/verification.py"


def test_package_declares_cap_007_reconciliation_ownership():
    package_docstring = capability.__doc__ or ""
    domain_docstring = capability.domain.__doc__ or ""
    assert "CAP-007" in package_docstring
    assert "Reconciliation" in package_docstring
    assert "CAP-007" in domain_docstring
    assert "Reconciliation" in domain_docstring
    assert "independent capability" not in package_docstring.lower()
    assert "independent capability" not in domain_docstring.lower()


def test_verification_has_only_authorized_public_domain_dependencies():
    source = VERIFICATION_SOURCE.read_text()
    assert "quant_platform.internal_economic_reality" in source
    assert "quant_platform.external_economic_observation" in source
    assert "InstrumentReference" in source and "CurrencyReference" in source
    forbidden = (
        "quant_platform.execution",
        "quant_platform.reconciliation",
        "PortfolioState",
        "Resolution",
        "Correction",
        "ReconciledState",
        "OperationalPolicy",
        "database",
        "broker",
        "network",
    )
    assert not any(word in source for word in forbidden)
    assert hasattr(capability, "verify_economic_reality")


def test_verification_reuses_source_identities_without_new_contracts():
    source = VERIFICATION_SOURCE.read_text()
    assert "from quant_platform.core import CurrencyReference, InstrumentReference" in source
    assert "class Portfolio" not in source
    assert "ReferenceTime" not in source


def test_package_contains_no_productive_infrastructure_or_later_responsibilities():
    productive_sources = "\n".join(path.read_text() for path in PACKAGE.rglob("*.py"))
    forbidden = (
        "resolve_discrepancy",
        "correct_portfolio",
        "reconciled_state",
        "operational_policy",
        "sqlalchemy",
        "requests.",
        "httpx.",
    )
    assert not any(word in productive_sources.lower() for word in forbidden)


def test_preceding_capabilities_are_unchanged_by_verification_dependency():
    for relative in (
        "src/quant_platform/internal_economic_reality",
        "src/quant_platform/external_economic_observation",
        "src/quant_platform/portfolio",
    ):
        for path in (ROOT / relative).rglob("*.py"):
            assert "economic_reality_verification" not in path.read_text()
