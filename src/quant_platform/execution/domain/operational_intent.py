"""Immutable operational planning derived from a Target PortfolioState."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import TYPE_CHECKING

from quant_platform.core import InstrumentReference
from quant_platform.portfolio import PortfolioState

from .exceptions import ExecutionDomainError

if TYPE_CHECKING:
    from quant_platform.operational_request import OperationalRequest


def _canonical_decimal(value: Decimal) -> str:
    return str(value.normalize())


class OperationDirection(str, Enum):
    """The only operational directions authorized by IT-034-001."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class InvestmentOperation:
    """An instrumental operation required to approach a target state."""

    instrument: InstrumentReference
    direction: OperationDirection
    quantity: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.instrument, InstrumentReference):
            raise ExecutionDomainError(
                "InvestmentOperation requires a public InstrumentReference."
            )
        if not isinstance(self.direction, OperationDirection):
            raise ExecutionDomainError(
                "InvestmentOperation direction must be BUY or SELL."
            )
        if (
            not isinstance(self.quantity, Decimal)
            or not self.quantity.is_finite()
            or self.quantity <= 0
        ):
            raise ExecutionDomainError(
                "InvestmentOperation quantity must be an exact, finite, positive Decimal."
            )


def _position_quantities(state: PortfolioState) -> dict[InstrumentReference, Decimal]:
    return {position.instrument: position.quantity for position in state.positions}


def _monetary_amounts(state: PortfolioState) -> dict[object, Decimal]:
    return {balance.currency: balance.amount for balance in state.monetary_balances}


@dataclass(frozen=True, slots=True, init=False, eq=False)
class OperationalIntent:
    """The complete instrumental plan for one Target PortfolioState."""

    target_portfolio_state: PortfolioState
    operations: tuple[InvestmentOperation, ...]
    semantic_identity: str

    def __init__(self, target_portfolio_state: PortfolioState) -> None:
        if not isinstance(target_portfolio_state, PortfolioState):
            raise ExecutionDomainError(
                "OperationalIntent requires one public Target PortfolioState."
            )
        current = target_portfolio_state.current_portfolio_state
        if not isinstance(current, PortfolioState):
            raise ExecutionDomainError(
                "Target PortfolioState requires one public current PortfolioState."
            )
        if not target_portfolio_state.considered_risk_evaluation_results:
            raise ExecutionDomainError(
                "Target PortfolioState requires accessible Risk provenance."
            )

        current_quantities = _position_quantities(current)
        target_quantities = _position_quantities(target_portfolio_state)
        operations = []
        for instrument in sorted(
            set(current_quantities) | set(target_quantities),
            key=lambda value: value.semantic_identity,
        ):
            delta = target_quantities.get(
                instrument, Decimal(0)
            ) - current_quantities.get(instrument, Decimal(0))
            if delta:
                operations.append(
                    InvestmentOperation(
                        instrument=instrument,
                        direction=(
                            OperationDirection.BUY
                            if delta > 0
                            else OperationDirection.SELL
                        ),
                        quantity=abs(delta),
                    )
                )
        canonical_operations = tuple(operations)

        monetary_change = _monetary_amounts(current) != _monetary_amounts(
            target_portfolio_state
        )
        if monetary_change and not canonical_operations:
            raise ExecutionDomainError(
                "An autonomous monetary transformation is not representable by "
                "InvestmentOperation."
            )

        identity = self._identity_for(target_portfolio_state, canonical_operations)
        object.__setattr__(self, "target_portfolio_state", target_portfolio_state)
        object.__setattr__(self, "operations", canonical_operations)
        object.__setattr__(self, "semantic_identity", identity)

    @staticmethod
    def _identity_for(
        target: PortfolioState,
        operations: tuple[InvestmentOperation, ...],
    ) -> str:
        current = target.current_portfolio_state
        canonical = json.dumps(
            {
                "basis": target.determination_basis_reference,
                "contributors": [
                    result.semantic_identity
                    for result in target.contributing_risk_evaluation_results
                ],
                "current": current.semantic_identity if current is not None else None,
                "operations": [
                    [
                        operation.instrument.semantic_identity,
                        operation.direction.value,
                        _canonical_decimal(operation.quantity),
                    ]
                    for operation in operations
                ],
                "target": target.semantic_identity,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def _identity_components(self) -> tuple[object, ...]:
        target = self.target_portfolio_state
        return (
            target.semantic_identity,
            target.current_portfolio_state,
            target.contributing_risk_evaluation_results,
            target.determination_basis_reference,
            self.operations,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OperationalIntent):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)


def prepare_operational_request(
    target_portfolio_state: PortfolioState,
) -> "OperationalRequest":
    """Prepare one complete request without crossing an external boundary."""
    from quant_platform.operational_request import OperationalRequest

    return OperationalRequest(OperationalIntent(target_portfolio_state))
