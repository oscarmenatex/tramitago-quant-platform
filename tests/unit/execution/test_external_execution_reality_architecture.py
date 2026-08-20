from pathlib import Path

import quant_platform.execution as execution
from quant_platform.core import CurrencyReference
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    ExternalExecutionAuthority,
    ExternalExecutionReality,
    InvestmentOperation,
    ReportedExecution,
    SupportingExecutionEvidence,
    qualify_external_execution_reality,
)


def test_required_contracts_are_importable_from_execution() -> None:
    assert execution.ExternalExecutionAuthority is ExternalExecutionAuthority
    assert execution.ExecutionRealityReferenceTime is ExecutionRealityReferenceTime
    assert execution.ReportedExecution is ReportedExecution
    assert execution.SupportingExecutionEvidence is SupportingExecutionEvidence
    assert execution.ExternalExecutionReality is ExternalExecutionReality
    assert execution.ExecutionDomainError is ExecutionDomainError
    assert (
        execution.qualify_external_execution_reality
        is qualify_external_execution_reality
    )


def test_contracts_reuse_authorized_public_types() -> None:
    assert ReportedExecution.__annotations__["currency"] is CurrencyReference
    assert SupportingExecutionEvidence.__annotations__["operation"] is InvestmentOperation
    assert tuple(qualify_external_execution_reality.__annotations__) == (
        "evidence",
        "return",
    )


def test_slice_has_cap_007_reconciliation_ownership_without_new_capability() -> None:
    source = Path("src/quant_platform/execution/external_reality.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "quant_platform.portfolio",
        "quant_platform.economic_reality_verification",
        "OperationalMaterialization",
        "ExecutionCompletionState",
        "ExternalEconomicObservation",
        "ReconciliationResult",
        "OrderReconciliation",
        "PortfolioState",
        "Event",
        "adapter",
        "broker",
        "network",
        "database",
        "filesystem",
        "message queue",
    )
    assert not any(term in source for term in forbidden)
    assert not Path("src/quant_platform/external_execution_reality").exists()
