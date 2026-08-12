"""Immutable public representation of one complete portfolio state."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.decision_model import DecisionProposal
from quant_platform.risk import RiskEvaluationOutcome, RiskEvaluationResult

from .exceptions import (
    DuplicatePortfolioComponentError,
    InvalidPortfolioComponentError,
    InvalidPortfolioTraceabilityError,
)


def _validate_material_decimal(value: object, label: str) -> Decimal:
    if not isinstance(value, Decimal) or not value.is_finite() or value.is_zero():
        raise InvalidPortfolioComponentError(
            f"{label} must be an exact, finite, non-zero Decimal."
        )
    return value


def _canonical_decimal(value: Decimal) -> str:
    return str(value.normalize())


@dataclass(frozen=True, slots=True)
class PortfolioPosition:
    instrument: InstrumentReference
    quantity: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise InvalidPortfolioComponentError(
                "A public InstrumentReference is required."
            )
        _validate_material_decimal(self.quantity, "Position quantity")


@dataclass(frozen=True, slots=True)
class MonetaryBalance:
    currency: CurrencyReference
    amount: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.currency, CurrencyReference):
            raise InvalidPortfolioComponentError(
                "A public CurrencyReference is required."
            )
        _validate_material_decimal(self.amount, "Monetary amount")


@dataclass(frozen=True, slots=True, init=False, eq=False)
class PortfolioState:
    positions: tuple[PortfolioPosition, ...]
    monetary_balances: tuple[MonetaryBalance, ...]
    decision_proposal: DecisionProposal | None
    risk_evaluation_result: RiskEvaluationResult | None
    current_portfolio_state: "PortfolioState | None"
    semantic_identity: str

    def __init__(
        self,
        positions: Iterable[PortfolioPosition] = (),
        monetary_balances: Iterable[MonetaryBalance] = (),
        *,
        decision_proposal: DecisionProposal | None = None,
        risk_evaluation_result: RiskEvaluationResult | None = None,
        current_portfolio_state: "PortfolioState | None" = None,
    ) -> None:
        try:
            supplied_positions = tuple(positions)
            supplied_balances = tuple(monetary_balances)
        except TypeError:
            raise InvalidPortfolioComponentError(
                "Portfolio components must be finite iterables."
            ) from None
        if any(not isinstance(item, PortfolioPosition) for item in supplied_positions):
            raise InvalidPortfolioComponentError(
                "Positions must contain only PortfolioPosition values."
            )
        if any(not isinstance(item, MonetaryBalance) for item in supplied_balances):
            raise InvalidPortfolioComponentError(
                "Monetary balances must contain only MonetaryBalance values."
            )

        instruments = [item.instrument for item in supplied_positions]
        currencies = [item.currency for item in supplied_balances]
        if len(set(instruments)) != len(instruments):
            raise DuplicatePortfolioComponentError(
                "Only one position per instrument is allowed."
            )
        if len(set(currencies)) != len(currencies):
            raise DuplicatePortfolioComponentError(
                "Only one monetary balance per currency is allowed."
            )

        canonical_positions = tuple(
            sorted(supplied_positions, key=lambda item: item.instrument.semantic_identity)
        )
        canonical_balances = tuple(
            sorted(supplied_balances, key=lambda item: item.currency.semantic_identity)
        )
        self._validate_traceability(
            decision_proposal, risk_evaluation_result, current_portfolio_state
        )
        identity = self._identity_for(canonical_positions, canonical_balances)
        object.__setattr__(self, "positions", canonical_positions)
        object.__setattr__(self, "monetary_balances", canonical_balances)
        object.__setattr__(self, "decision_proposal", decision_proposal)
        object.__setattr__(self, "risk_evaluation_result", risk_evaluation_result)
        object.__setattr__(self, "current_portfolio_state", current_portfolio_state)
        object.__setattr__(self, "semantic_identity", identity)

    @staticmethod
    def _validate_traceability(
        proposal: DecisionProposal | None,
        risk_result: RiskEvaluationResult | None,
        current_state: "PortfolioState | None",
    ) -> None:
        values = proposal, risk_result, current_state
        if all(item is None for item in values):
            return
        if not isinstance(proposal, DecisionProposal):
            raise InvalidPortfolioTraceabilityError(
                "Complete traceability requires a public DecisionProposal."
            )
        if not isinstance(risk_result, RiskEvaluationResult):
            raise InvalidPortfolioTraceabilityError(
                "Complete traceability requires a public RiskEvaluationResult."
            )
        if not isinstance(current_state, PortfolioState):
            raise InvalidPortfolioTraceabilityError(
                "Complete traceability requires a current PortfolioState."
            )
        if risk_result.decision_proposal != proposal:
            raise InvalidPortfolioTraceabilityError(
                "RiskEvaluationResult must correspond to DecisionProposal."
            )
        if risk_result.outcome is RiskEvaluationOutcome.REJECTED:
            raise InvalidPortfolioTraceabilityError(
                "A REJECTED Risk result cannot produce a Portfolio State."
            )

    @staticmethod
    def _identity_for(
        positions: tuple[PortfolioPosition, ...],
        balances: tuple[MonetaryBalance, ...],
    ) -> str:
        canonical = json.dumps(
            {
                "monetary_balances": [
                    [item.currency.semantic_identity, _canonical_decimal(item.amount)]
                    for item in balances
                ],
                "positions": [
                    [item.instrument.semantic_identity, _canonical_decimal(item.quantity)]
                    for item in positions
                ],
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def _identity_components(self) -> tuple[object, ...]:
        return self.positions, self.monetary_balances

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PortfolioState):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)
