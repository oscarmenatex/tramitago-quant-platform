from dataclasses import FrozenInstanceError

import pytest

from quant_platform.core import CurrencyReference, InvalidCurrencyReferenceError


def test_constructs_valid_reference() -> None:
    assert CurrencyReference("USD").currency_code == "USD"


def test_canonicalizes_code_to_uppercase() -> None:
    assert CurrencyReference("eur").currency_code == "EUR"


@pytest.mark.parametrize("code", [None, 1])
def test_rejects_absent_or_non_string_code(code: object) -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference(code)  # type: ignore[arg-type]


def test_rejects_empty_code() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("")


def test_rejects_leading_whitespace() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference(" USD")


def test_rejects_trailing_whitespace() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("USD ")


def test_rejects_short_code() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("US")


def test_rejects_long_code() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("USDD")


def test_rejects_numeric_characters() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("U1D")


def test_rejects_special_characters() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("U$D")


def test_rejects_non_ascii_letters() -> None:
    with pytest.raises(InvalidCurrencyReferenceError):
        CurrencyReference("ÑSD")


def test_equivalent_constructions_are_equal() -> None:
    assert CurrencyReference("usd") == CurrencyReference("USD")


def test_different_codes_are_unequal() -> None:
    assert CurrencyReference("USD") != CurrencyReference("EUR")


def test_hash_is_consistent_with_equality() -> None:
    assert hash(CurrencyReference("usd")) == hash(CurrencyReference("USD"))


def test_is_immutable_and_disallows_dynamic_attributes() -> None:
    reference = CurrencyReference("USD")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        reference.currency_code = "EUR"  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError, TypeError)):
        reference.provider = "vendor"  # type: ignore[attr-defined]


def test_semantic_identity_is_reproducible() -> None:
    assert CurrencyReference("usd").semantic_identity == CurrencyReference("USD").semantic_identity
