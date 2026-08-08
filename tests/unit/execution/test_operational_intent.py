from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    InvestmentOperation,
    OperationalIntent,
    OperationDirection,
)
from quant_platform.core import InstrumentReference
from quant_platform.portfolio_transition import PortfolioTransition


def test_materializes_every_position_transition_exactly_once(
    transition: PortfolioTransition,
) -> None:
    intent = OperationalIntent(transition)

    assert intent.portfolio_transition is transition
    assert len(intent.operations) == len(transition.position_transitions) == 2
    assert [operation.instrument for operation in intent.operations] == [
        component.instrument for component in transition.position_transitions
    ]


def test_positive_delta_is_buy_and_negative_delta_is_sell(
    transition: PortfolioTransition,
) -> None:
    operations = {item.instrument.identification_value: item for item in OperationalIntent(transition).operations}

    assert operations["BUY-ME"].direction is OperationDirection.BUY
    assert operations["BUY-ME"].quantity == Decimal("3")
    assert operations["SELL-ME"].direction is OperationDirection.SELL
    assert operations["SELL-ME"].quantity == Decimal("2")


def test_monetary_transition_does_not_create_an_operation(
    transition: PortfolioTransition,
) -> None:
    intent = OperationalIntent(transition)

    operation_instruments = {item.instrument for item in intent.operations}
    assert len(intent.operations) == len(transition.position_transitions)
    assert all(
        component.currency not in operation_instruments
        for component in transition.monetary_transitions
    )


def test_monetary_only_transition_produces_complete_empty_operation_set() -> None:
    from quant_platform.core import CurrencyReference
    from quant_platform.portfolio import MonetaryBalance, PortfolioState
    from quant_platform.portfolio_transition import PortfolioMonetaryTransition

    currency = CurrencyReference("USD")
    current = PortfolioState(
        monetary_balances=(MonetaryBalance(currency, Decimal("10")),)
    )
    target = PortfolioState(
        monetary_balances=(MonetaryBalance(currency, Decimal("15")),)
    )
    transition = PortfolioTransition(
        current,
        target,
        monetary_transitions=(PortfolioMonetaryTransition(currency, Decimal("5")),),
    )

    assert OperationalIntent(transition).operations == ()


@pytest.mark.parametrize("invalid", [None, object(), "transition"])
def test_rejects_a_missing_or_invalid_origin(invalid: object) -> None:
    with pytest.raises(ExecutionDomainError):
        OperationalIntent(invalid)  # type: ignore[arg-type]


def test_contract_and_components_are_immutable(
    transition: PortfolioTransition,
) -> None:
    intent = OperationalIntent(transition)

    with pytest.raises((FrozenInstanceError, AttributeError)):
        intent.operations = ()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        intent.operations[0].quantity = Decimal("99")  # type: ignore[misc]


def test_identity_is_stable_and_independent_from_instance_identity(
    transition: PortfolioTransition,
) -> None:
    first = OperationalIntent(transition)
    second = OperationalIntent(transition)

    assert first is not second
    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity
    assert first.semantic_identity != transition.semantic_identity


def test_public_fields_are_exact() -> None:
    assert [field.name for field in fields(OperationalIntent)] == [
        "portfolio_transition",
        "operations",
        "semantic_identity",
    ]


@pytest.mark.parametrize(
    ("instrument", "direction", "quantity"),
    [
        ("FIGI:A", OperationDirection.BUY, Decimal("1")),
        (InstrumentReference("FIGI", "A"), "BUY", Decimal("1")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, Decimal("0")),
        (InstrumentReference("FIGI", "A"), OperationDirection.SELL, Decimal("-1")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, Decimal("NaN")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, 1),
    ],
)
def test_investment_operation_rejects_invalid_public_values(
    instrument: object,
    direction: object,
    quantity: object,
) -> None:
    with pytest.raises(ExecutionDomainError):
        InvestmentOperation(instrument, direction, quantity)  # type: ignore[arg-type]
