"""Immutable public representation of one complete portfolio state."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json

from quant_platform.core import CurrencyReference, InstrumentReference
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
    current_portfolio_state: "PortfolioState | None"
    considered_risk_evaluation_results: tuple[RiskEvaluationResult, ...]
    contributing_risk_evaluation_results: tuple[RiskEvaluationResult, ...]
    determination_basis_reference: str | None
    semantic_identity: str

    def __init__(
        self,
        positions: Iterable[PortfolioPosition] = (),
        monetary_balances: Iterable[MonetaryBalance] = (),
        *,
        current_portfolio_state: "PortfolioState | None" = None,
        considered_risk_evaluation_results: Iterable[RiskEvaluationResult] = (),
        contributing_risk_evaluation_results: Iterable[RiskEvaluationResult] = (),
        determination_basis_reference: str | None = None,
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
            sorted(
                supplied_positions, key=lambda item: item.instrument.semantic_identity
            )
        )
        canonical_balances = tuple(
            sorted(supplied_balances, key=lambda item: item.currency.semantic_identity)
        )
        considered, contributing, basis = self._validate_provenance(
            current_portfolio_state,
            considered_risk_evaluation_results,
            contributing_risk_evaluation_results,
            determination_basis_reference,
        )
        object.__setattr__(self, "positions", canonical_positions)
        object.__setattr__(self, "monetary_balances", canonical_balances)
        object.__setattr__(self, "current_portfolio_state", current_portfolio_state)
        object.__setattr__(self, "considered_risk_evaluation_results", considered)
        object.__setattr__(self, "contributing_risk_evaluation_results", contributing)
        object.__setattr__(self, "determination_basis_reference", basis)
        object.__setattr__(
            self,
            "semantic_identity",
            self._identity_for(canonical_positions, canonical_balances),
        )

    @staticmethod
    def _validate_provenance(
        current: "PortfolioState | None",
        considered: Iterable[RiskEvaluationResult],
        contributing: Iterable[RiskEvaluationResult],
        basis: str | None,
    ) -> tuple[
        tuple[RiskEvaluationResult, ...], tuple[RiskEvaluationResult, ...], str | None
    ]:
        try:
            considered_values = tuple(considered)
            contributing_values = tuple(contributing)
        except TypeError:
            raise InvalidPortfolioTraceabilityError(
                "Target provenance collections must be finite iterables."
            ) from None
        present = (
            current is not None
            or considered_values
            or contributing_values
            or basis is not None
        )
        if not present:
            return (), (), None
        if not isinstance(current, PortfolioState):
            raise InvalidPortfolioTraceabilityError(
                "Target provenance requires a current PortfolioState."
            )
        if not considered_values or any(
            not isinstance(x, RiskEvaluationResult) for x in considered_values
        ):
            raise InvalidPortfolioTraceabilityError(
                "Target provenance requires considered Risk results."
            )
        if any(x.outcome is RiskEvaluationOutcome.REJECTED for x in considered_values):
            raise InvalidPortfolioTraceabilityError(
                "Target provenance cannot contain REJECTED Risk results."
            )
        if any(not isinstance(x, RiskEvaluationResult) for x in contributing_values):
            raise InvalidPortfolioTraceabilityError(
                "Target contributors must be Risk results."
            )
        if len(set(considered_values)) != len(considered_values) or len(
            set(contributing_values)
        ) != len(contributing_values):
            raise InvalidPortfolioTraceabilityError(
                "Target provenance cannot contain duplicates."
            )
        if not set(contributing_values).issubset(set(considered_values)):
            raise InvalidPortfolioTraceabilityError("Contributors must be considered.")
        if not isinstance(basis, str) or not basis.strip():
            raise InvalidPortfolioTraceabilityError(
                "A non-empty determination basis is required."
            )

        def canonical(
            values: tuple[RiskEvaluationResult, ...],
        ) -> tuple[RiskEvaluationResult, ...]:
            return tuple(sorted(values, key=lambda x: x.semantic_identity))

        return canonical(considered_values), canonical(contributing_values), basis

    @staticmethod
    def _identity_for(
        positions: tuple[PortfolioPosition, ...], balances: tuple[MonetaryBalance, ...]
    ) -> str:
        canonical = json.dumps(
            {
                "monetary_balances": [
                    [x.currency.semantic_identity, _canonical_decimal(x.amount)]
                    for x in balances
                ],
                "positions": [
                    [x.instrument.semantic_identity, _canonical_decimal(x.quantity)]
                    for x in positions
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
