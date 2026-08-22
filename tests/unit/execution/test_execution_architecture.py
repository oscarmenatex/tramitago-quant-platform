from pathlib import Path

import quant_platform.execution as execution
from quant_platform.core import InstrumentReference
from quant_platform.execution import (
    ExecutionCompletionState,
    ExecutionCompletionStatus,
    InvestmentOperation,
    OperationalIntent,
    classify_execution_completion,
)
from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretation,
)
from quant_platform.portfolio import PortfolioState


def test_public_api_is_limited_to_the_authorized_contract() -> None:
    assert execution.__all__ == [
        "CapitalProtectionAuthority",
        "CapitalProtectionReferenceTime",
        "ExecutionCompletionState",
        "ExecutionCompletionStatus",
        "ExecutionDomainError",
        "ExecutionRealityReferenceTime",
        "ExecutionRealityVerification",
        "ExecutionRealityVerificationOutcome",
        "ExternalFailure",
        "ExternalFailureCapitalProtectionCondition",
        "ExternalFailureCapitalProtectionQualification",
        "ExternalFailureAuthority",
        "ExternalFailureClass",
        "ExternalFailureObligation",
        "ExternalFailureReferenceTime",
        "ExternalExecutionAuthority",
        "ExternalExecutionReality",
        "ExternalOrderReality",
        "ExternalOrderRealityAuthority",
        "ExternalOrderAuthority",
        "ExternalOrderTerminalState",
        "InternalExecutionAuthority",
        "InternalExecutionReality",
        "InternalOrderReality",
        "InternalOrderRealityAuthority",
        "InvestmentOperation",
        "OperationalIntent",
        "OperationDirection",
        "OrderLifecycleMeaning",
        "OrderRealityVerification",
        "OrderRealityVerificationOutcome",
        "OrderRealityReferenceTime",
        "OrderTerminalReferenceTime",
        "OrderTerminalState",
        "ReportedExecution",
        "ReconciliationReferenceTime",
        "ReconciliationCompletionCondition",
        "ReconciliationCompletionQualification",
        "RequiredReconciliationScope",
        "SupportingExecutionEvidence",
        "SupportingCapitalProtectionEvidence",
        "SupportingExternalFailureEvidence",
        "SupportingExternalOrderRealityEvidence",
        "SupportingInternalExecutionEvidence",
        "SupportingInternalOrderRealityEvidence",
        "SupportingOrderTerminalEvidence",
        "classify_execution_completion",
        "declare_required_reconciliation_scope",
        "prepare_operational_request",
        "qualify_external_execution_reality",
        "qualify_external_failure_capital_protection",
        "qualify_external_order_reality",
        "qualify_internal_execution_reality",
        "qualify_internal_order_reality",
        "qualify_reconciliation_completion",
        "recognize_external_failure",
        "recognize_order_terminal_state",
        "verify_execution_reality",
        "verify_order_reality",
    ]


def test_public_contract_reuses_only_authorized_domain_contracts() -> None:
    assert OperationalIntent.__annotations__["target_portfolio_state"] is PortfolioState
    assert InvestmentOperation.__annotations__["instrument"] is InstrumentReference
    assert (
        ExecutionCompletionState.__annotations__["interpretation"]
        is OperationalMaterializationInterpretation
    )


def test_completion_contract_has_only_partial_and_complete() -> None:
    assert list(ExecutionCompletionStatus) == [
        ExecutionCompletionStatus.PARTIAL,
        ExecutionCompletionStatus.COMPLETE,
    ]
    assert tuple(classify_execution_completion.__annotations__) == (
        "interpretation",
        "return",
    )


def test_completion_has_no_later_responsibilities_or_infrastructure() -> None:
    source = Path("src/quant_platform/execution/completion.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "remaining_quantity",
        "completion_ratio",
        "current_completion",
        "latest_completion",
        "Reconciliation",
        "PortfolioState",
        "Event",
        "broker",
        "database",
        "repository",
        "message queue",
    )
    assert not any(term in source for term in forbidden)


def test_capability_contains_no_infrastructure_or_materialization_layers() -> None:
    root = Path("src/quant_platform/execution")
    paths = tuple(root.rglob("*"))
    forbidden_names = {
        "adapter",
        "adapters",
        "broker",
        "infrastructure",
        "market",
        "persistence",
        "protocol",
        "repository",
        "service",
        "strategy",
    }
    assert not any(path.name.lower() in forbidden_names for path in paths)

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py"
    )
    forbidden_dependencies = (
        "quant_platform.decision_model",
        "quant_platform.risk",
        "quant_platform.portfolio_transition",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)
