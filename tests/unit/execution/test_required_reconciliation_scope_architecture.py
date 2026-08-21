from pathlib import Path

import quant_platform.execution as execution


def test_exact_new_public_api_is_available_from_execution() -> None:
    expected = {
        "ReconciliationReferenceTime",
        "RequiredReconciliationScope",
        "declare_required_reconciliation_scope",
    }
    assert expected <= set(execution.__all__)
    assert all(getattr(execution, name) is not None for name in expected)


def test_slice_stays_inside_execution_and_stops_at_required_scope() -> None:
    assert not Path("src/quant_platform/reconciliation").exists()
    source = Path("src/quant_platform/execution/reconciliation_scope.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "EconomicRealityVerification",
        "ExecutionRealityVerification",
        "OrderRealityVerification",
        "NOT_RECONCILED",
        "RECONCILED",
        "diagnosis",
        "resolution",
        "PortfolioState",
        "Event",
        "adapter",
        "broker",
        "database",
        "repository",
        "infrastructure",
        "current_time",
        "creation_time",
        "processing_time",
    )
    assert not any(term in source for term in forbidden)
