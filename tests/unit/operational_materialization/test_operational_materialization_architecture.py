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
    assert OperationalMaterialization.__annotations__["operation"] is InvestmentOperation
    assert (
        OperationalMaterializationObservation.__annotations__["operation"]
        is InvestmentOperation
    )
    assert (
        OperationalMaterializationBoundary.observe.__annotations__["admission"]
        is OperationalAdmission
    )


def test_capability_has_no_productive_infrastructure_or_later_responsibilities() -> None:
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
