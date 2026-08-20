from pathlib import Path

import quant_platform.operational_request as operational_request
from quant_platform.execution import InvestmentOperation, OperationalIntent
from quant_platform.operational_request import OperationalRequest


def test_public_api_is_limited_to_authorized_contracts() -> None:
    assert operational_request.__all__ == [
        "OperationalRequest",
        "OperationalRequestDomainError",
    ]


def test_public_contract_reuses_execution_contracts() -> None:
    assert OperationalRequest.__annotations__["operational_intent"] is OperationalIntent
    assert (
        OperationalRequest.__annotations__["operations"]
        == tuple[InvestmentOperation, ...]
    )


def test_dependency_direction_and_infrastructure_independence() -> None:
    root = Path("src/quant_platform/operational_request")
    paths = tuple(root.rglob("*"))
    forbidden_names = {
        "adapter",
        "adapters",
        "broker",
        "gateway",
        "infrastructure",
        "persistence",
        "protocol",
        "repository",
        "service",
        "transport",
    }
    assert not any(path.name.lower() in forbidden_names for path in paths)

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py"
    )
    forbidden_dependencies = (
        "quant_platform.data",
        "quant_platform.portfolio",
        "quant_platform.portfolio_transition",
        "quant_platform.risk",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)

    execution_paths = tuple(Path("src/quant_platform/execution").rglob("*.py"))
    execution_source_without_terminal_recognition = "\n".join(
        path.read_text(encoding="utf-8")
        for path in execution_paths
        if path.name != "order_terminal_state.py"
    )
    assert (
        "quant_platform.operational_submission"
        not in execution_source_without_terminal_recognition
    )
    terminal_recognition_source = Path(
        "src/quant_platform/execution/order_terminal_state.py"
    ).read_text(encoding="utf-8")
    assert "quant_platform.operational_submission" in terminal_recognition_source
