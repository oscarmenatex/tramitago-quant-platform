from pathlib import Path

import quant_platform.execution as execution
from quant_platform.core import InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationalIntent
from quant_platform.portfolio_transition import PortfolioTransition


def test_public_api_is_limited_to_the_authorized_contract() -> None:
    assert execution.__all__ == [
        "ExecutionDomainError",
        "InvestmentOperation",
        "OperationalIntent",
        "OperationDirection",
    ]


def test_public_contract_reuses_only_authorized_domain_contracts() -> None:
    assert OperationalIntent.__annotations__["portfolio_transition"] is PortfolioTransition
    assert InvestmentOperation.__annotations__["instrument"] is InstrumentReference


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
        "quant_platform.portfolio ",
        "quant_platform.risk",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)
