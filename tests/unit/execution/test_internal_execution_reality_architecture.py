from pathlib import Path

import quant_platform.execution as execution
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    InternalExecutionAuthority,
    InternalExecutionReality,
    InvestmentOperation,
    SupportingInternalExecutionEvidence,
    qualify_internal_execution_reality,
)
from quant_platform.operational_materialization import OperationalMaterialization


def test_required_contracts_are_importable_from_execution() -> None:
    assert execution.InternalExecutionAuthority is InternalExecutionAuthority
    assert execution.SupportingInternalExecutionEvidence is (
        SupportingInternalExecutionEvidence
    )
    assert execution.InternalExecutionReality is InternalExecutionReality
    assert execution.ExecutionRealityReferenceTime is ExecutionRealityReferenceTime
    assert execution.InvestmentOperation is InvestmentOperation
    assert execution.ExecutionDomainError is ExecutionDomainError
    assert (
        execution.qualify_internal_execution_reality
        is qualify_internal_execution_reality
    )


def test_contracts_reuse_authorized_public_types() -> None:
    annotations = SupportingInternalExecutionEvidence.__annotations__
    assert annotations["reference_time"] is ExecutionRealityReferenceTime
    assert annotations["operation"] is InvestmentOperation
    assert annotations["materializations"] == tuple[OperationalMaterialization, ...]
    assert tuple(qualify_internal_execution_reality.__annotations__) == (
        "evidence",
        "return",
    )


def test_slice_remains_cap_007_reconciliation_without_downstream_responsibility() -> None:
    source = Path("src/quant_platform/execution/internal_reality.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "InternalExecutionReferenceTime",
        "ReportedInternalExecution",
        "InternalFill",
        "ExternalExecutionReality",
        "ReportedExecution",
        "OperationalMaterializationInterpretation",
        "ExecutionCompletionState",
        "quant_platform.portfolio",
        "quant_platform.economic_reality_verification",
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
    assert not Path("src/quant_platform/internal_execution_reality").exists()
