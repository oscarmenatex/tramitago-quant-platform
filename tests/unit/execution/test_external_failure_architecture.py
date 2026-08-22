from pathlib import Path

import quant_platform.execution as execution


def test_exact_new_public_surface_is_exported() -> None:
    expected = {
        "ExternalFailureClass",
        "ExternalFailureObligation",
        "ExternalFailureAuthority",
        "ExternalFailureReferenceTime",
        "SupportingExternalFailureEvidence",
        "ExternalFailure",
        "recognize_external_failure",
    }
    assert expected <= set(execution.__all__)
    assert all(getattr(execution, name) is not None for name in expected)


def test_external_failure_has_no_inference_or_negative_scope() -> None:
    source = Path("src/quant_platform/execution/external_failure.py").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "AdmissionDecision",
        "ExternalOrderTerminalState",
        "OperationalMaterialization",
        "VerificationOutcome",
        "ReconciliationCompletionQualification",
        "ExternalFailureId",
        "correlation",
        "provider taxonomy",
        "diagnosis",
        "retry",
        "resubmission",
        "severity",
        "priority",
        "recoverability",
        "alert",
        "incident",
        "persistence",
        "event bus",
        "Knowledge Core",
        "current_failure",
        "latest_failure",
        "current_reconciliation",
        "latest_reconciliation",
        "broker",
        "SDK",
        "timeout",
        "freshness",
    )
    assert not any(term in source for term in forbidden)


def test_unrelated_facts_errors_and_outcomes_do_not_create_failure() -> None:
    source = Path("src/quant_platform/execution/external_failure.py").read_text(
        encoding="utf-8"
    )
    for unrelated in (
        "REJECTED",
        "CANCELLED",
        "EXPIRED",
        "DISCREPANCY",
        "DIVERGENT",
        "INSUFFICIENT_EVIDENCE",
    ):
        assert unrelated not in source
    assert "except Exception" not in source.split(
        "def recognize_external_failure", maxsplit=1
    )[1]
