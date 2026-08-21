from pathlib import Path

import quant_platform.execution as execution
from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderReality,
    InternalOrderReality,
    OrderRealityVerification,
    OrderRealityVerificationOutcome,
    verify_order_reality,
)


def test_exact_public_api_is_importable() -> None:
    assert execution.OrderRealityVerification is OrderRealityVerification
    assert execution.OrderRealityVerificationOutcome is OrderRealityVerificationOutcome
    assert execution.verify_order_reality is verify_order_reality
    assert ExecutionDomainError is execution.ExecutionDomainError


def test_contract_reuses_both_source_realities() -> None:
    assert OrderRealityVerification.__annotations__ == {
        "internal_reality": InternalOrderReality,
        "external_reality": ExternalOrderReality,
        "outcome": OrderRealityVerificationOutcome,
    }
    assert tuple(verify_order_reality.__annotations__) == (
        "internal_reality",
        "external_reality",
        "return",
    )


def test_verification_has_no_inverse_dependency() -> None:
    root = Path("src/quant_platform/execution")
    for name in ("internal_order_reality.py", "order_reality.py"):
        assert "order_reality_verification" not in (root / name).read_text(
            encoding="utf-8"
        )


def test_slice_stops_at_verification() -> None:
    source = Path(
        "src/quant_platform/execution/order_reality_verification.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "NOT_COMPARABLE",
        "RECONCILED",
        "diagnosis",
        "resolution",
        "missing_meanings",
        "extra_meanings",
        "Portfolio",
        "Event",
        "adapter",
        "broker",
        "database",
        "repository",
        "infrastructure",
    )
    assert not any(term in source for term in forbidden)
