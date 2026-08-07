"""Immutable public representation of an authorized portfolio transition."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import PortfolioState

from .exceptions import (
    DuplicatePortfolioTransitionComponentError,
    InvalidPortfolioTransitionComponentError,
    InvalidPortfolioTransitionRelationError,
)


def _validate_delta(value: object, label: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or value.is_zero():
        raise InvalidPortfolioTransitionComponentError(
            f"{label} must be an exact, finite, non-zero Decimal."
        )
    return value


def _canonical_decimal(value: Decimal) -> str:
    return str(value.normalize())


@dataclass(frozen=True, slots=True)
class PortfolioPositionTransition:
    instrument: InstrumentReference
    quantity_delta: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise InvalidPortfolioTransitionComponentError(
                "A public InstrumentReference is required."
            )
        _validate_delta(self.quantity_delta, "Quantity delta")


@dataclass(frozen=True, slots=True)
class PortfolioMonetaryTransition:
    currency: CurrencyReference
    amount_delta: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.currency, CurrencyReference):
            raise InvalidPortfolioTransitionComponentError(
                "A public CurrencyReference is required."
            )
        _validate_delta(self.amount_delta, "Amount delta")


@dataclass(frozen=True, slots=True, init=False, eq=False)
class PortfolioTransition:
    current_portfolio_state: PortfolioState
    target_portfolio_state: PortfolioState
    position_transitions: tuple[PortfolioPositionTransition, ...]
    monetary_transitions: tuple[PortfolioMonetaryTransition, ...]

    def __init__(
        self,
        current_portfolio_state: PortfolioState,
        target_portfolio_state: PortfolioState,
        position_transitions: Iterable[PortfolioPositionTransition] = (),
        monetary_transitions: Iterable[PortfolioMonetaryTransition] = (),
    ) -> None:
        if not isinstance(current_portfolio_state, PortfolioState):
            raise InvalidPortfolioTransitionRelationError(
                "Current portfolio state must be a public PortfolioState."
            )
        if not isinstance(target_portfolio_state, PortfolioState):
            raise InvalidPortfolioTransitionRelationError(
                "Target portfolio state must be a public PortfolioState."
            )

        supplied_positions = self._materialize(position_transitions, "Position")
        supplied_money = self._materialize(monetary_transitions, "Monetary")
        if any(
            not isinstance(item, PortfolioPositionTransition)
            for item in supplied_positions
        ):
            raise InvalidPortfolioTransitionComponentError(
                "Position transitions must contain only PortfolioPositionTransition values."
            )
        if any(
            not isinstance(item, PortfolioMonetaryTransition)
            for item in supplied_money
        ):
            raise InvalidPortfolioTransitionComponentError(
                "Monetary transitions must contain only PortfolioMonetaryTransition values."
            )

        instruments = [item.instrument for item in supplied_positions]
        currencies = [item.currency for item in supplied_money]
        if len(set(instruments)) != len(instruments):
            raise DuplicatePortfolioTransitionComponentError(
                "Only one transition per instrument is allowed."
            )
        if len(set(currencies)) != len(currencies):
            raise DuplicatePortfolioTransitionComponentError(
                "Only one transition per currency is allowed."
            )

        canonical_positions = tuple(
            sorted(
                supplied_positions,
                key=lambda item: item.instrument.semantic_identity,
            )
        )
        canonical_money = tuple(
            sorted(supplied_money, key=lambda item: item.currency.semantic_identity)
        )
        self._validate_relation(
            current_portfolio_state,
            target_portfolio_state,
            canonical_positions,
            canonical_money,
        )
        object.__setattr__(self, "current_portfolio_state", current_portfolio_state)
        object.__setattr__(self, "target_portfolio_state", target_portfolio_state)
        object.__setattr__(self, "position_transitions", canonical_positions)
        object.__setattr__(self, "monetary_transitions", canonical_money)

    @staticmethod
    def _materialize(values: object, label: str) -> tuple[object, ...]:
        try:
            return tuple(values)  # type: ignore[arg-type]
        except TypeError:
            raise InvalidPortfolioTransitionComponentError(
                f"{label} transitions must be finite iterables."
            ) from None

    @staticmethod
    def _validate_relation(
        current: PortfolioState,
        target: PortfolioState,
        positions: tuple[PortfolioPositionTransition, ...],
        money: tuple[PortfolioMonetaryTransition, ...],
    ) -> None:
        if not positions and not money:
            raise InvalidPortfolioTransitionRelationError(
                "A portfolio transition requires at least one material change."
            )

        current_positions = {item.instrument: item.quantity for item in current.positions}
        target_positions = {item.instrument: item.quantity for item in target.positions}
        expected_positions = {
            instrument: target_positions.get(instrument, Decimal(0))
            - current_positions.get(instrument, Decimal(0))
            for instrument in current_positions.keys() | target_positions.keys()
        }
        expected_positions = {
            instrument: delta
            for instrument, delta in expected_positions.items()
            if not delta.is_zero()
        }
        declared_positions = {
            item.instrument: item.quantity_delta for item in positions
        }

        current_money = {
            item.currency: item.amount for item in current.monetary_balances
        }
        target_money = {item.currency: item.amount for item in target.monetary_balances}
        expected_money = {
            currency: target_money.get(currency, Decimal(0))
            - current_money.get(currency, Decimal(0))
            for currency in current_money.keys() | target_money.keys()
        }
        expected_money = {
            currency: delta
            for currency, delta in expected_money.items()
            if not delta.is_zero()
        }
        declared_money = {item.currency: item.amount_delta for item in money}

        if declared_positions != expected_positions or declared_money != expected_money:
            raise InvalidPortfolioTransitionRelationError(
                "Declared transitions must exactly match every material state difference."
            )

    @property
    def semantic_identity(self) -> str:
        """Return the reproducible identity of the complete relation."""
        canonical = json.dumps(
            {
                "current_portfolio_state": self.current_portfolio_state.semantic_identity,
                "monetary_transitions": [
                    [item.currency.semantic_identity, _canonical_decimal(item.amount_delta)]
                    for item in self.monetary_transitions
                ],
                "position_transitions": [
                    [
                        item.instrument.semantic_identity,
                        _canonical_decimal(item.quantity_delta),
                    ]
                    for item in self.position_transitions
                ],
                "target_portfolio_state": self.target_portfolio_state.semantic_identity,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def _identity_components(self) -> tuple[object, ...]:
        return (
            self.current_portfolio_state,
            self.target_portfolio_state,
            self.position_transitions,
            self.monetary_transitions,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortfolioTransition):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)
