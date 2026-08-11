from pathlib import Path

import quant_platform.operational_materialization_interpretation as capability
from quant_platform.execution import InvestmentOperation
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretation,
)


def test_public_api_is_exactly_the_authorized_contract() -> None:
    assert capability.__all__ == [
        "OperationalMaterializationInterpretation",
        "interpret_materializations",
        "OperationalMaterializationInterpretationDomainError",
    ]


def test_contract_reuses_only_authorized_preceding_types() -> None:
    annotations = OperationalMaterializationInterpretation.__annotations__
    assert annotations["operation"] is InvestmentOperation
    assert annotations["source_materializations"] == tuple[
        OperationalMaterialization, ...
    ]


def test_core_has_no_preceding_flow_later_domain_or_infrastructure_dependency() -> None:
    root = Path("src/quant_platform/operational_materialization_interpretation")
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in root.rglob("*.py")
    ).lower()
    forbidden = (
        "quant_platform.portfolio",
        "operational_request",
        "operational_submission",
        "operational_admission",
        "reconciliation",
        "broker",
        "repository",
        "boundary",
        "observation",
        "remaining_quantity",
        "average_price",
        "completion",
    )
    assert not any(item in source for item in forbidden)
