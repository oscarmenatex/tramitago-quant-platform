from pathlib import Path

import quant_platform.portfolio_transition as portfolio_transition
from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def test_public_exports_are_exact() -> None:
    assert portfolio_transition.__all__ == [
        "DuplicatePortfolioTransitionComponentError",
        "InvalidPortfolioTransitionComponentError",
        "InvalidPortfolioTransitionRelationError",
        "PortfolioMonetaryTransition",
        "PortfolioPositionTransition",
        "PortfolioTransition",
        "PortfolioTransitionError",
    ]


def test_reuses_exact_public_contracts() -> None:
    assert PortfolioPositionTransition.__annotations__["instrument"] is InstrumentReference
    assert PortfolioMonetaryTransition.__annotations__["currency"] is CurrencyReference
    assert PortfolioTransition.__annotations__["current_portfolio_state"] is PortfolioState
    assert PortfolioTransition.__annotations__["target_portfolio_state"] is PortfolioState


def test_capability_has_no_forbidden_layers_or_generation_api() -> None:
    root = Path("src/quant_platform/portfolio_transition")
    paths = tuple(root.rglob("*"))
    forbidden_names = {
        "service", "services", "repository", "repositories", "registry",
        "persistence", "infrastructure", "factory", "execution", "broker", "market",
    }
    assert not any(path.name.lower() in forbidden_names for path in paths)
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in paths if path.suffix == ".py"
    )
    assert "quant_platform.execution" not in source
    assert "from_states" not in source
    assert "calculate_transition" not in source
