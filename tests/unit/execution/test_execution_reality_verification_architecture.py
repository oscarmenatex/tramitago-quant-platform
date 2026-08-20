from pathlib import Path

import quant_platform.execution as execution
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityVerification,
    ExecutionRealityVerificationOutcome,
    ExternalExecutionReality,
    InternalExecutionReality,
    verify_execution_reality,
)


def test_normative_api_is_importable_from_execution() -> None:
    assert execution.ExecutionRealityVerificationOutcome is (
        ExecutionRealityVerificationOutcome
    )
    assert execution.ExecutionRealityVerification is ExecutionRealityVerification
    assert execution.ExecutionDomainError is ExecutionDomainError
    assert execution.verify_execution_reality is verify_execution_reality


def test_contract_depends_on_both_source_realities() -> None:
    annotations = ExecutionRealityVerification.__annotations__
    assert annotations == {
        "internal_reality": InternalExecutionReality,
        "external_reality": ExternalExecutionReality,
        "outcome": ExecutionRealityVerificationOutcome,
    }


def test_slice_remains_cap_007_reconciliation_without_later_responsibilities() -> None:
    source = Path("src/quant_platform/execution/reality_verification.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "NOT_COMPARABLE",
        "RECONCILED",
        "matching",
        "missing_internal",
        "missing_external",
        "quantity_delta",
        "price_delta",
        "corrective",
        "OrderReconciliation",
        "PortfolioState",
        "Event",
        "economic_reality_verification",
        "adapter",
        "broker",
        "network",
        "database",
        "filesystem",
        "message queue",
    )
    assert not any(term in source for term in forbidden)
    assert not Path("src/quant_platform/execution_reality_verification").exists()


def test_source_realities_do_not_depend_on_verification() -> None:
    for name in ("internal_reality.py", "external_reality.py"):
        source = Path("src/quant_platform/execution", name).read_text(encoding="utf-8")
        assert "reality_verification" not in source
        assert "ExecutionRealityVerification" not in source
