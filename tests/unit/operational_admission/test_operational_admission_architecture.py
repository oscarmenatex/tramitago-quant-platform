from pathlib import Path

import quant_platform.operational_admission as operational_admission
from quant_platform.operational_admission import (
    OperationalAdmission,
    OperationalAdmissionBoundary,
    OperationalAdmissionObservation,
)
from quant_platform.operational_submission import OperationalSubmission


def test_public_api_is_exactly_the_authorized_contract() -> None:
    assert operational_admission.__all__ == [
        "OperationalAdmission",
        "AdmissionDecision",
        "OperationalAdmissionObservation",
        "OperationalAdmissionBoundary",
        "recognize_admission",
        "OperationalAdmissionDomainError",
    ]


def test_admission_reuses_the_submission_contract() -> None:
    assert OperationalAdmission.__annotations__["submission"] is OperationalSubmission
    assert (
        OperationalAdmissionBoundary.observe.__annotations__["submission"]
        is OperationalSubmission
    )
    assert (
        OperationalAdmissionBoundary.observe.__annotations__["return"]
        is OperationalAdmissionObservation
    )


def test_dependency_direction_and_infrastructure_independence() -> None:
    root = Path("src/quant_platform/operational_admission")
    paths = tuple(root.rglob("*"))
    forbidden_names = {
        "adapter",
        "adapters",
        "broker",
        "gateway",
        "infrastructure",
        "persistence",
        "repository",
        "transport",
    }
    assert not any(path.name.lower() in forbidden_names for path in paths)

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py"
    )
    forbidden_dependencies = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "quant_platform.data",
        "quant_platform.execution",
        "quant_platform.portfolio",
        "quant_platform.portfolio_transition",
        "quant_platform.risk",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)

    submission_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/operational_submission").rglob("*.py")
    )
    assert "quant_platform.operational_admission" not in submission_source


def test_no_economic_materialization_or_later_responsibilities_are_modeled() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/operational_admission").rglob("*.py")
    ).lower()
    forbidden_contracts = (
        "execution_price",
        "executed_quantity",
        "partial_fill",
        "settlement",
        "portfolio_state",
        "reconciliation",
        "retry",
    )
    assert not any(contract in source for contract in forbidden_contracts)
