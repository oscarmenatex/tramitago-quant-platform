"""Immutable public operational intent derived from a portfolio transition."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json

from quant_platform.core import InstrumentReference
from quant_platform.portfolio_transition import PortfolioTransition

from .exceptions import ExecutionDomainError


def _canonical_decimal(value: Decimal) -> str:
    return str(value.normalize())


class OperationDirection(str, Enum):
    """The only operational directions authorized by IT-034-001."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True, slots=True)
class InvestmentOperation:
    """A constituent operation owned by one operational intent."""

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


@dataclass(frozen=True, slots=True, init=False, eq=False)
class OperationalIntent:
    """The complete operational meaning of one PortfolioTransition."""

    portfolio_transition: PortfolioTransition
    operations: tuple[InvestmentOperation, ...]
    semantic_identity: str

    def __init__(self, portfolio_transition: PortfolioTransition) -> None:
        if not isinstance(portfolio_transition, PortfolioTransition):
            raise ExecutionDomainError(
                "OperationalIntent requires one public PortfolioTransition."
            )

        operations = tuple(
            InvestmentOperation(
                instrument=component.instrument,
                direction=(
                    OperationDirection.BUY
                    if component.quantity_delta > 0
                    else OperationDirection.SELL
                ),
                quantity=abs(component.quantity_delta),
            )
            for component in portfolio_transition.position_transitions
        )
        identity = self._identity_for(portfolio_transition, operations)
        object.__setattr__(self, "portfolio_transition", portfolio_transition)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "semantic_identity", identity)

    @staticmethod
    def _identity_for(
        transition: PortfolioTransition,
        operations: tuple[InvestmentOperation, ...],
    ) -> str:
        canonical = json.dumps(
            {
                "operations": [
                    [
                        operation.instrument.semantic_identity,
                        operation.direction.value,
                        _canonical_decimal(operation.quantity),
                    ]
                    for operation in operations
                ],
                "portfolio_transition": transition.semantic_identity,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    @property
    def _identity_components(self) -> tuple[object, ...]:
        return self.portfolio_transition, self.operations

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OperationalIntent):
            return NotImplemented
        return self._identity_components == other._identity_components

    def __hash__(self) -> int:
        return hash(self._identity_components)
