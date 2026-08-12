from pathlib import Path

import quant_platform.post_materialization_economic_consequence as capability
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.portfolio import PortfolioState
from quant_platform.post_materialization_economic_consequence import (
    PostMaterializationEconomicConsequence,
)


def test_capability_is_separate_and_public_api_is_exact() -> None:
    assert capability.__all__ == [
        "PostMaterializationEconomicConsequence",
        "derive_post_materialization_consequence",
        "PostMaterializationEconomicConsequenceDomainError",
    ]


def test_asset_reuses_authorized_public_contracts() -> None:
    annotations = PostMaterializationEconomicConsequence.__annotations__
    assert annotations["previous_portfolio_state"] is PortfolioState
    assert annotations["source_materializations"] == tuple[
        OperationalMaterialization, ...
    ]
    assert annotations["resulting_portfolio_state"] is PortfolioState


def test_capability_has_no_infrastructure_or_excluded_responsibilities() -> None:
    root = Path("src/quant_platform/post_materialization_economic_consequence")
    source = "\n".join(path.read_text() for path in root.rglob("*.py")).lower()
    forbidden = (
        "operational_materialization_interpretation",
        "portfolio_transition",
        "settlement",
        "reconciliation",
        "profit",
        "loss",
        "remaining_quantity",
        "average_price",
        "repository",
        "database",
        "broker",
        "requests",
    )
    assert not any(item in source for item in forbidden)


def test_preceding_capabilities_do_not_depend_on_new_capability() -> None:
    for name in (
        "portfolio",
        "portfolio_transition",
        "execution",
        "operational_materialization",
        "operational_materialization_interpretation",
    ):
        source = "\n".join(
            path.read_text()
            for path in Path(f"src/quant_platform/{name}").rglob("*.py")
        )
        assert "post_materialization_economic_consequence" not in source
