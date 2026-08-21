from pathlib import Path

import quant_platform.execution as execution
from quant_platform.execution import (
    ExecutionDomainError,
    ExternalOrderTerminalState,
    InternalOrderReality,
    InternalOrderRealityAuthority,
    OrderLifecycleMeaning,
    OrderRealityReferenceTime,
    SupportingInternalOrderRealityEvidence,
    qualify_internal_order_reality,
)
from quant_platform.operational_admission import OperationalAdmission
from quant_platform.operational_submission import OperationalSubmission


def test_exact_new_public_api_is_importable() -> None:
    assert execution.InternalOrderRealityAuthority is InternalOrderRealityAuthority
    assert execution.SupportingInternalOrderRealityEvidence is (
        SupportingInternalOrderRealityEvidence
    )
    assert execution.InternalOrderReality is InternalOrderReality
    assert execution.qualify_internal_order_reality is qualify_internal_order_reality


def test_contract_annotations_reuse_only_authorized_types() -> None:
    annotations = SupportingInternalOrderRealityEvidence.__annotations__
    assert annotations == {
        "authority": InternalOrderRealityAuthority,
        "reference_time": OrderRealityReferenceTime,
        "observed_at_utc": __import__("datetime").datetime,
        "submission": OperationalSubmission,
        "meanings": frozenset[OrderLifecycleMeaning],
        "supporting_facts": tuple[
            OperationalAdmission | ExternalOrderTerminalState, ...
        ],
    }
    assert "authority" not in InternalOrderReality.__annotations__
    assert ExecutionDomainError is execution.ExecutionDomainError


def test_slice_stays_cap_007_reconciliation_only() -> None:
    source = Path("src/quant_platform/execution/internal_order_reality.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "ExternalOrderReality",
        "AGREEMENT",
        "DISCREPANCY",
        "OrderRealityVerification",
        "ReportedExecution",
        "OperationalMaterialization",
        "ExecutionCompletionState",
        "PortfolioState",
        "Event",
        "current_status",
        "latest_status",
        "effective_status",
        "correlation_id",
        "broker",
        "adapter",
        "database",
        "repository",
        "infrastructure",
    )
    assert not any(term in source for term in forbidden)
    assert not Path("src/quant_platform/internal_order_reality").exists()
