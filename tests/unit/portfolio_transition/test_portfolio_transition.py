from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    DuplicatePortfolioTransitionComponentError,
    InvalidPortfolioTransitionComponentError,
    InvalidPortfolioTransitionRelationError,
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def position_change(instrument: InstrumentReference, value: str = "2") -> PortfolioPositionTransition:
    return PortfolioPositionTransition(instrument, Decimal(value))


def money_change(currency: CurrencyReference, value: str = "-20") -> PortfolioMonetaryTransition:
    return PortfolioMonetaryTransition(currency, Decimal(value))


def test_valid_mixed_transition_preserves_states(
    current_state: PortfolioState,
    target_state: PortfolioState,
    instrument: InstrumentReference,
    currency: CurrencyReference,
) -> None:
    transition = PortfolioTransition(
        current_state,
        target_state,
        (position_change(instrument),),
        (money_change(currency),),
    )
    assert transition.current_portfolio_state is current_state
    assert transition.target_portfolio_state is target_state


def test_valid_position_only_transition(instrument: InstrumentReference) -> None:
    current = PortfolioState((PortfolioPosition(instrument, Decimal("1")),))
    target = PortfolioState((PortfolioPosition(instrument, Decimal("2")),))
    assert PortfolioTransition(current, target, (position_change(instrument, "1"),))


def test_valid_monetary_only_transition(currency: CurrencyReference) -> None:
    current = PortfolioState(monetary_balances=(MonetaryBalance(currency, Decimal("1")),))
    target = PortfolioState(monetary_balances=(MonetaryBalance(currency, Decimal("2")),))
    assert PortfolioTransition(
        current, target, monetary_transitions=(money_change(currency, "1"),)
    )


@pytest.mark.parametrize("endpoint", [None, object(), "state"])
def test_rejects_invalid_current(endpoint: object, target_state: PortfolioState) -> None:
    with pytest.raises(InvalidPortfolioTransitionRelationError):
        PortfolioTransition(endpoint, target_state)  # type: ignore[arg-type]


@pytest.mark.parametrize("endpoint", [None, object(), "state"])
def test_rejects_invalid_target(endpoint: object, current_state: PortfolioState) -> None:
    with pytest.raises(InvalidPortfolioTransitionRelationError):
        PortfolioTransition(current_state, endpoint)  # type: ignore[arg-type]


def test_rejects_empty_transition(current_state: PortfolioState) -> None:
    with pytest.raises(InvalidPortfolioTransitionRelationError):
        PortfolioTransition(current_state, current_state)


def test_rejects_invalid_collection_item(
    current_state: PortfolioState, target_state: PortfolioState
) -> None:
    with pytest.raises(InvalidPortfolioTransitionComponentError):
        PortfolioTransition(current_state, target_state, (object(),))  # type: ignore[arg-type]


def test_rejects_duplicate_instrument(
    current_state: PortfolioState,
    target_state: PortfolioState,
    instrument: InstrumentReference,
) -> None:
    duplicate = position_change(instrument)
    with pytest.raises(DuplicatePortfolioTransitionComponentError):
        PortfolioTransition(current_state, target_state, (duplicate, duplicate))


def test_rejects_duplicate_currency(
    current_state: PortfolioState,
    target_state: PortfolioState,
    currency: CurrencyReference,
) -> None:
    duplicate = money_change(currency)
    with pytest.raises(DuplicatePortfolioTransitionComponentError):
        PortfolioTransition(
            current_state,
            target_state,
            monetary_transitions=(duplicate, duplicate),
        )


def test_rejects_incorrect_delta(
    current_state: PortfolioState,
    target_state: PortfolioState,
    instrument: InstrumentReference,
    currency: CurrencyReference,
) -> None:
    with pytest.raises(InvalidPortfolioTransitionRelationError):
        PortfolioTransition(
            current_state,
            target_state,
            (position_change(instrument, "3"),),
            (money_change(currency),),
        )


def test_rejects_non_exhaustive_transition(
    current_state: PortfolioState,
    target_state: PortfolioState,
    instrument: InstrumentReference,
) -> None:
    with pytest.raises(InvalidPortfolioTransitionRelationError):
        PortfolioTransition(
            current_state, target_state, (position_change(instrument),)
        )


def test_absent_identity_is_zero_for_relation() -> None:
    instrument = InstrumentReference("FIGI", "NEW")
    current = PortfolioState(monetary_balances=(MonetaryBalance(CurrencyReference("USD"), Decimal("1")),))
    target = PortfolioState((PortfolioPosition(instrument, Decimal("5")),))
    transition = PortfolioTransition(
        current,
        target,
        (position_change(instrument, "5"),),
        (PortfolioMonetaryTransition(CurrencyReference("USD"), Decimal("-1")),),
    )
    assert transition.position_transitions[0].quantity_delta == 5


def test_canonical_order_is_input_independent() -> None:
    a = InstrumentReference("FIGI", "A")
    b = InstrumentReference("FIGI", "B")
    current = PortfolioState((PortfolioPosition(a, Decimal("1")), PortfolioPosition(b, Decimal("1"))))
    target = PortfolioState((PortfolioPosition(a, Decimal("2")), PortfolioPosition(b, Decimal("3"))))
    first = PortfolioTransition(current, target, (position_change(a, "1"), position_change(b, "2")))
    second = PortfolioTransition(current, target, (position_change(b, "2"), position_change(a, "1")))
    assert first == second
    assert first.position_transitions == second.position_transitions
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity


def test_equivalent_decimals_have_same_identity() -> None:
    instrument = InstrumentReference("FIGI", "A")
    current = PortfolioState((PortfolioPosition(instrument, Decimal("1")),))
    target_one = PortfolioState((PortfolioPosition(instrument, Decimal("2")),))
    target_two = PortfolioState((PortfolioPosition(instrument, Decimal("2.00")),))
    one = PortfolioTransition(current, target_one, (position_change(instrument, "1.0"),))
    two = PortfolioTransition(current, target_two, (position_change(instrument, "1.00"),))
    assert one == two
    assert hash(one) == hash(two)
    assert one.semantic_identity == two.semantic_identity


def test_identity_changes_with_endpoint() -> None:
    instrument = InstrumentReference("FIGI", "A")
    start = PortfolioState((PortfolioPosition(instrument, Decimal("1")),))
    middle = PortfolioState((PortfolioPosition(instrument, Decimal("2")),))
    end = PortfolioState((PortfolioPosition(instrument, Decimal("3")),))
    assert PortfolioTransition(start, middle, (position_change(instrument, "1"),)) != PortfolioTransition(middle, end, (position_change(instrument, "1"),))


def test_transition_is_immutable(
    current_state: PortfolioState,
    target_state: PortfolioState,
    instrument: InstrumentReference,
    currency: CurrencyReference,
) -> None:
    transition = PortfolioTransition(current_state, target_state, (position_change(instrument),), (money_change(currency),))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        transition.position_transitions = ()  # type: ignore[misc]


def test_public_fields_are_exact() -> None:
    assert [field.name for field in fields(PortfolioTransition)] == [
        "current_portfolio_state",
        "target_portfolio_state",
        "position_transitions",
        "monetary_transitions",
    ]
