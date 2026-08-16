from pathlib import Path

import quant_platform.operational_materialization as operational_materialization
from quant_platform.execution import InvestmentOperation
from quant_platform.operational_admission import OperationalAdmission
from quant_platform.operational_materialization import (
    OperationalMaterialization,
    OperationalMaterializationBoundary,
    OperationalMaterializationObservation,
)


def test_public_api_is_exactly_the_authorized_contract() -> None:
    assert operational_materialization.__all__ == [
        "OperationalMaterialization",
        "OperationalMaterializationObservation",
        "OperationalMaterializationBoundary",
        "recognize_materialization",
        "OperationalMaterializationDomainError",
    ]


def test_contracts_reuse_preceding_public_types() -> None:
    assert OperationalMaterialization.__annotations__["occurrence_id"] is str
    assert OperationalMaterializationObservation.__annotations__["occurrence_id"] is str
    assert (
        OperationalMaterialization.__annotations__["operation"] is InvestmentOperation
    )
    assert (
        OperationalMaterializationObservation.__annotations__["operation"]
        is InvestmentOperation
    )
    assert (
        OperationalMaterializationBoundary.observe.__annotations__["admission"]
        is OperationalAdmission
    )


def test_execution_responsibility_has_no_infrastructure_or_later_work() -> None:
    root = Path("src/quant_platform/operational_materialization")
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
    ).lower()
    forbidden = (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "quant_platform.portfolio",
        "reconciliation",
        "settlement",
        "cumulative_quantity",
        "remaining_quantity",
        "average_price",
        "completion_state",
        "retry",
    )
    assert not any(item in source for item in forbidden)

    admission_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/quant_platform/operational_admission").rglob("*.py")
    )
    assert "quant_platform.operational_materialization" not in admission_source


def test_materialization_is_described_as_an_execution_responsibility() -> None:
    package_source = Path(
        "src/quant_platform/operational_materialization/__init__.py"
    ).read_text(encoding="utf-8")
    domain_source = Path(
        "src/quant_platform/operational_materialization/domain/__init__.py"
    ).read_text(encoding="utf-8")

    assert "within Execution" in package_source
    assert "within Execution" in domain_source
    assert "Materialization capability" not in package_source
    assert "owned by Operational Materialization" not in domain_source
