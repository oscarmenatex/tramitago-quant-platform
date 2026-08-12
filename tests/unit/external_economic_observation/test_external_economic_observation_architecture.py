import ast
from decimal import Decimal
from pathlib import Path

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.external_economic_observation import (
    ObservedMonetaryAssertion,
    ObservedPositionAssertion,
)


PACKAGE = Path("src/quant_platform/external_economic_observation")


def test_capability_is_separate_and_reuses_reference_contracts_directly():
    position = ObservedPositionAssertion(
        InstrumentReference("figi", "A"), Decimal("1")
    )
    monetary = ObservedMonetaryAssertion(CurrencyReference("USD"), Decimal("1"))
    assert type(position.instrument) is InstrumentReference
    assert type(monetary.currency) is CurrencyReference


def test_capability_has_no_forbidden_architectural_dependencies():
    forbidden = {
        "portfolio",
        "execution",
        "operational_materialization",
        "operational_materialization_interpretation",
        "post_materialization_economic_consequence",
        "database",
        "broker",
        "reconciliation",
        "trust",
    }
    for path in PACKAGE.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        imported.update(
            name.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for name in node.names
        )
        assert not any(word in module for module in imported for word in forbidden)
