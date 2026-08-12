from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationDirection
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.post_materialization_economic_consequence import (
    PostMaterializationEconomicConsequence,
    PostMaterializationEconomicConsequenceDomainError,
    derive_post_materialization_consequence,
)


def _position(state: PortfolioState, instrument: InstrumentReference) -> Decimal | None:
    return next((x.quantity for x in state.positions if x.instrument == instrument), None)


def _balance(state: PortfolioState, currency: CurrencyReference) -> Decimal | None:
    return next((x.amount for x in state.monetary_balances if x.currency == currency), None)


@pytest.mark.parametrize(
    ("direction", "expected_position", "expected_cash"),
    [
        (OperationDirection.BUY, Decimal("12"), Decimal("950")),
        (OperationDirection.SELL, Decimal("8"), Decimal("1050")),
    ],
)
def test_positive_price_applies_position_and_gross_monetary_consequence(
    instrument, usd, materialization_factory, direction, expected_position, expected_cash
) -> None:
    previous = PortfolioState(
        (PortfolioPosition(instrument, Decimal("10")),),
        (MonetaryBalance(usd, Decimal("1000")),),
    )
    source = materialization_factory(direction, "2", "25")

    consequence = derive_post_materialization_consequence(previous, [source])

    assert _position(consequence.resulting_portfolio_state, instrument) == expected_position
    assert _balance(consequence.resulting_portfolio_state, usd) == expected_cash


def test_materialization_quantity_is_authoritative(instrument, materialization_factory) -> None:
    source = materialization_factory(
        OperationDirection.BUY, "3", "10", operation_quantity="100"
    )
    result = derive_post_materialization_consequence(PortfolioState(), [source])
    assert _position(result.resulting_portfolio_state, instrument) == Decimal("3")


@pytest.mark.parametrize("direction", list(OperationDirection))
def test_zero_price_does_not_fabricate_zero_balance(
    instrument, usd, materialization_factory, direction
) -> None:
    source = materialization_factory(direction, "2", "0")
    result = derive_post_materialization_consequence(PortfolioState(), [source])
    assert _balance(result.resulting_portfolio_state, usd) is None


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (OperationDirection.BUY, Decimal("30")),
        (OperationDirection.SELL, Decimal("-30")),
    ],
)
def test_negative_price_follows_algebraic_rule(
    usd, materialization_factory, direction, expected
) -> None:
    source = materialization_factory(direction, "3", "-10")
    result = derive_post_materialization_consequence(PortfolioState(), [source])
    assert _balance(result.resulting_portfolio_state, usd) == expected


def test_multiple_facts_combine_by_instrument_and_currency(
    instrument, usd, materialization_factory
) -> None:
    sources = (
        materialization_factory(OperationDirection.BUY, "4", "10"),
        materialization_factory(OperationDirection.SELL, "1", "15"),
    )
    result = derive_post_materialization_consequence(PortfolioState(), sources)
    state = result.resulting_portfolio_state
    assert state.positions == (PortfolioPosition(instrument, Decimal("3")),)
    assert state.monetary_balances == (MonetaryBalance(usd, Decimal("-25")),)


def test_source_input_order_has_no_public_contractual_meaning(
    materialization_factory,
) -> None:
    first = materialization_factory(OperationDirection.BUY, "4", "10")
    second = materialization_factory(OperationDirection.SELL, "1", "15")
    previous = PortfolioState()

    forward = derive_post_materialization_consequence(previous, [first, second])
    reversed_input = derive_post_materialization_consequence(previous, [second, first])

    assert forward.resulting_portfolio_state == reversed_input.resulting_portfolio_state
    assert forward.source_materializations == reversed_input.source_materializations
    assert forward == reversed_input
    assert hash(forward) == hash(reversed_input)


def test_multiple_instruments_and_currencies_do_not_apply_fx(materialization_factory) -> None:
    eur = CurrencyReference("EUR")
    other = InstrumentReference("FIGI", "OTHER")
    usd_source = materialization_factory(OperationDirection.BUY, "2", "10")
    eur_source = materialization_factory(
        OperationDirection.SELL, "3", "7", currency=eur, source_instrument=other
    )

    state = derive_post_materialization_consequence(
        PortfolioState(), [usd_source, eur_source]
    ).resulting_portfolio_state

    assert len(state.positions) == 2
    assert _balance(state, CurrencyReference("USD")) == Decimal("-20")
    assert _balance(state, eur) == Decimal("21")


def test_fully_zero_result_is_valid_empty_state(instrument, usd, materialization_factory) -> None:
    previous = PortfolioState(
        (PortfolioPosition(instrument, Decimal("10")),),
        (MonetaryBalance(usd, Decimal("-100")),),
    )
    source = materialization_factory(OperationDirection.SELL, "10", "10")
    state = derive_post_materialization_consequence(previous, [source]).resulting_portfolio_state
    assert state == PortfolioState()
    assert state.positions == () and state.monetary_balances == ()


def test_zero_sources_and_incompatible_inputs_are_domain_errors() -> None:
    with pytest.raises(PostMaterializationEconomicConsequenceDomainError):
        derive_post_materialization_consequence(PortfolioState(), [])
    with pytest.raises(PostMaterializationEconomicConsequenceDomainError):
        derive_post_materialization_consequence(object(), [object()])  # type: ignore[arg-type]


def test_asset_exposes_complete_provenance_and_rejects_arbitrary_s1(
    instrument, materialization_factory
) -> None:
    previous = PortfolioState()
    source = materialization_factory(OperationDirection.BUY, "2", "10")
    valid = derive_post_materialization_consequence(previous, [source])
    assert valid.previous_portfolio_state is previous
    assert valid.source_materializations == (source,)
    assert _position(valid.resulting_portfolio_state, instrument) == Decimal("2")
    with pytest.raises(PostMaterializationEconomicConsequenceDomainError):
        PostMaterializationEconomicConsequence(previous, (source,), PortfolioState())


def test_sources_and_previous_state_remain_unchanged_and_result_is_immutable(
    materialization_factory,
) -> None:
    previous = PortfolioState()
    source = materialization_factory(OperationDirection.BUY, "2", "10")
    source_values = (source.operation, source.quantity, source.price, source.currency)
    consequence = derive_post_materialization_consequence(previous, [source])
    assert previous == PortfolioState()
    assert source_values == (source.operation, source.quantity, source.price, source.currency)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        consequence.resulting_portfolio_state = PortfolioState()  # type: ignore[misc]
