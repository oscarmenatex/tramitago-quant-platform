from pathlib import Path

import quant_platform.portfolio as portfolio
from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


def test_public_export_is_minimal() -> None:
    assert portfolio.__all__ == [
        "DuplicatePortfolioComponentError", "InvalidPortfolioComponentError",
        "InvalidPortfolioTraceabilityError", "MonetaryBalance", "PortfolioPosition",
        "PortfolioState", "PortfolioStateError",
    ]


def test_reuses_exact_public_reference_contracts() -> None:
    assert PortfolioPosition.__annotations__["instrument"] is InstrumentReference
    assert MonetaryBalance.__annotations__["currency"] is CurrencyReference


def test_has_one_state_contract_and_no_roles() -> None:
    assert not hasattr(portfolio, "CurrentPortfolioState")
    assert not hasattr(portfolio, "TargetPortfolioState")
    assert not hasattr(portfolio, "PortfolioStateRole")
    assert "role" not in PortfolioState.__annotations__


def test_has_no_forbidden_layers_or_dependencies() -> None:
    root = Path("src/quant_platform/portfolio")
    paths = tuple(root.rglob("*"))
    assert not any(path.name.lower() in {"service", "services", "registry", "persistence", "infrastructure"} for path in paths)
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py")
    assert "quant_platform.execution" not in source
    assert "from quant_platform.core import" in source
