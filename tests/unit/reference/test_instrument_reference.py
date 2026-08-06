from dataclasses import FrozenInstanceError

import pytest

from quant_platform.core import (
    InstrumentReference,
    InvalidInstrumentReferenceError,
)


def test_constructs_valid_reference() -> None:
    assert InstrumentReference("FIGI", "BBG000B9XRY4").identification_value == "BBG000B9XRY4"


def test_canonicalizes_scheme_to_uppercase() -> None:
    assert InstrumentReference("figi", "value").identification_scheme == "FIGI"


def test_preserves_value_exactly() -> None:
    assert InstrumentReference("custom", "Ab-cD").identification_value == "Ab-cD"


@pytest.mark.parametrize("scheme", [None, 1])
def test_rejects_absent_or_non_string_scheme(scheme: object) -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference(scheme, "value")  # type: ignore[arg-type]


def test_rejects_empty_scheme() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("", "value")


def test_rejects_leading_scheme_whitespace() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference(" FIGI", "value")


def test_rejects_trailing_scheme_whitespace() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("FIGI ", "value")


@pytest.mark.parametrize("value", [None, 1])
def test_rejects_absent_or_non_string_value(value: object) -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("FIGI", value)  # type: ignore[arg-type]


def test_rejects_empty_value() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("FIGI", "")


def test_rejects_leading_value_whitespace() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("FIGI", " value")


def test_rejects_trailing_value_whitespace() -> None:
    with pytest.raises(InvalidInstrumentReferenceError):
        InstrumentReference("FIGI", "value ")


def test_equivalent_constructions_are_equal() -> None:
    assert InstrumentReference("figi", "value") == InstrumentReference("FIGI", "value")


def test_different_schemes_are_unequal() -> None:
    assert InstrumentReference("FIGI", "value") != InstrumentReference("ISIN", "value")


def test_different_values_are_unequal() -> None:
    assert InstrumentReference("FIGI", "one") != InstrumentReference("FIGI", "two")


def test_hash_is_consistent_with_equality() -> None:
    assert hash(InstrumentReference("figi", "value")) == hash(InstrumentReference("FIGI", "value"))


def test_is_immutable_and_disallows_dynamic_attributes() -> None:
    reference = InstrumentReference("FIGI", "value")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        reference.identification_value = "other"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        reference.provider = "vendor"  # type: ignore[attr-defined]


def test_semantic_identity_is_reproducible() -> None:
    assert InstrumentReference("figi", "value").semantic_identity == InstrumentReference("FIGI", "value").semantic_identity


def test_value_case_is_semantically_significant() -> None:
    assert InstrumentReference("FIGI", "AbC") != InstrumentReference("FIGI", "abc")
