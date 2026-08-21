from pathlib import Path

import quant_platform.execution as execution


def test_exact_new_public_api_is_available_from_execution() -> None:
    expected = {
        "ReconciliationCompletionCondition",
        "ReconciliationCompletionQualification",
        "qualify_reconciliation_completion",
    }
    assert expected <= set(execution.__all__)
    assert all(getattr(execution, name) is not None for name in expected)


def test_slice_stays_in_execution_without_later_responsibilities() -> None:
    assert not Path("src/quant_platform/reconciliation").exists()
    source = Path(
        "src/quant_platform/execution/reconciliation_completion.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        "diagnosis",
        "resolution",
        "corrective",
        "PortfolioState",
        "reconciled_at",
        "current_state",
        "latest_state",
        "Event",
        "alert",
        "incident",
        "retry",
        "broker",
        "adapter",
        "database",
        "repository",
        "queue",
        "scheduler",
        "network",
    )
    assert not any(term in source for term in forbidden)


def test_preceding_contracts_do_not_depend_on_completion_qualification() -> None:
    for name in (
        "reconciliation_scope.py",
        "reality_verification.py",
        "order_reality_verification.py",
    ):
        source = Path("src/quant_platform/execution", name).read_text(encoding="utf-8")
        assert "reconciliation_completion" not in source
        assert "ReconciliationCompletionQualification" not in source
