from dataclasses import fields
from pathlib import Path

import quant_platform.core as reference_contracts
from quant_platform.core import CurrencyReference, InstrumentReference


def test_public_export_is_minimal_and_explicit() -> None:
    assert reference_contracts.__all__ == [
        "CurrencyReference",
        "InstrumentReference",
        "InvalidCurrencyReferenceError",
        "InvalidInstrumentReferenceError",
        "ReferenceIdentityError",
    ]


def test_exactly_two_public_reference_contracts_exist() -> None:
    assert {CurrencyReference, InstrumentReference} == {
        item for item in vars(reference_contracts).values() if isinstance(item, type)
    } - {
        reference_contracts.ReferenceIdentityError,
        reference_contracts.InvalidInstrumentReferenceError,
        reference_contracts.InvalidCurrencyReferenceError,
    }


def test_contract_fields_are_exact() -> None:
    assert [field.name for field in fields(InstrumentReference)] == [
        "identification_scheme",
        "identification_value",
    ]
    assert [field.name for field in fields(CurrencyReference)] == ["currency_code"]


def test_contracts_are_not_interchangeable() -> None:
    assert InstrumentReference("ISO", "USD") != CurrencyReference("USD")


def test_namespace_is_neutral_and_has_no_capability_dependencies() -> None:
    source = Path("src/quant_platform/core/references.py").read_text(encoding="utf-8")
    assert InstrumentReference.__module__ == "quant_platform.core.references"
    for capability in (
        "data",
        "research",
        "strategy_evaluation",
        "decision_model",
        "risk",
        "portfolio",
        "execution",
    ):
        assert f"quant_platform.{capability}" not in source


def test_no_forbidden_reference_components_exist() -> None:
    root = Path("src/quant_platform/core")
    names = {path.stem.lower() for path in root.rglob("*.py")}
    assert not names & {"instrument", "currency", "catalog", "registry", "service"}
    assert not any(path.name in {"infrastructure", "persistence"} for path in root.rglob("*"))


def test_existing_public_contracts_are_untouched() -> None:
    assert Path("src/quant_platform/decision_model/__init__.py").read_text(encoding="utf-8").count("DecisionProposal") == 2
    assert "RiskEvaluationResult" in Path("src/quant_platform/risk/__init__.py").read_text(encoding="utf-8")
