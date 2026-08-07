from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio_transition import (
    InvalidPortfolioTransitionComponentError,
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
)


def test_valid_position_transition_reuses_reference(
    instrument: InstrumentReference,
) -> None:
    component = PortfolioPositionTransition(instrument, Decimal("2"))
    assert component.instrument is instrument
    assert component.quantity_delta == Decimal("2")


def test_position_transition_accepts_negative_delta(
    instrument: InstrumentReference,
) -> None:
    assert PortfolioPositionTransition(instrument, Decimal("-2")).quantity_delta < 0


@pytest.mark.parametrize(
    "value",
    [Decimal("0"), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), 1, 1.0, "1", None],
)
def test_position_transition_rejects_invalid_delta(
    instrument: InstrumentReference, value: object
) -> None:
    with pytest.raises(InvalidPortfolioTransitionComponentError):
        PortfolioPositionTransition(instrument, value)  # type: ignore[arg-type]


def test_position_transition_rejects_invalid_reference() -> None:
    with pytest.raises(InvalidPortfolioTransitionComponentError):
        PortfolioPositionTransition("FIGI:A", Decimal("1"))  # type: ignore[arg-type]


def test_position_transition_is_immutable(instrument: InstrumentReference) -> None:
    component = PortfolioPositionTransition(instrument, Decimal("1"))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        component.quantity_delta = Decimal("2")  # type: ignore[misc]


def test_valid_monetary_transition_reuses_reference(
    currency: CurrencyReference,
) -> None:
    component = PortfolioMonetaryTransition(currency, Decimal("-20"))
    assert component.currency is currency
    assert component.amount_delta == Decimal("-20")


def test_monetary_transition_accepts_positive_delta(
    currency: CurrencyReference,
) -> None:
    assert PortfolioMonetaryTransition(currency, Decimal("2")).amount_delta > 0


@pytest.mark.parametrize(
    "value",
    [Decimal("0"), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), 1, 1.0, "1", None],
)
def test_monetary_transition_rejects_invalid_delta(
    currency: CurrencyReference, value: object
) -> None:
    with pytest.raises(InvalidPortfolioTransitionComponentError):
        PortfolioMonetaryTransition(currency, value)  # type: ignore[arg-type]


def test_monetary_transition_rejects_invalid_reference() -> None:
    with pytest.raises(InvalidPortfolioTransitionComponentError):
        PortfolioMonetaryTransition("USD", Decimal("1"))  # type: ignore[arg-type]


def test_monetary_transition_is_immutable(currency: CurrencyReference) -> None:
    component = PortfolioMonetaryTransition(currency, Decimal("1"))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        component.amount_delta = Decimal("2")  # type: ignore[misc]
