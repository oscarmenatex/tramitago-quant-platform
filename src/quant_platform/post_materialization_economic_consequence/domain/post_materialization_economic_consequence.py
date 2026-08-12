"""Economic consequence derived from recognized material occurrences."""

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from quant_platform.execution import OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState

from .exceptions import PostMaterializationEconomicConsequenceDomainError


def _derive_state(
    previous_state: PortfolioState,
    sources: tuple[OperationalMaterialization, ...],
) -> PortfolioState:
    positions = {item.instrument: item.quantity for item in previous_state.positions}
    balances = {
        item.currency: item.amount for item in previous_state.monetary_balances
    }

    for source in sources:
        position_delta = source.quantity
        monetary_delta = source.quantity * source.price
        if source.operation.direction is OperationDirection.BUY:
            monetary_delta = -monetary_delta
        else:
            position_delta = -position_delta

        instrument = source.operation.instrument
        positions[instrument] = positions.get(instrument, Decimal("0")) + position_delta
        balances[source.currency] = (
            balances.get(source.currency, Decimal("0")) + monetary_delta
        )

    return PortfolioState(
        positions=(
            PortfolioPosition(instrument, quantity)
            for instrument, quantity in positions.items()
            if not quantity.is_zero()
        ),
        monetary_balances=(
            MonetaryBalance(currency, amount)
            for currency, amount in balances.items()
            if not amount.is_zero()
        ),
    )


@dataclass(frozen=True, slots=True)
class PostMaterializationEconomicConsequence:
    """Immutable causal relation between S0, recognized facts, and S1."""

    previous_portfolio_state: PortfolioState
    source_materializations: tuple[OperationalMaterialization, ...]
    resulting_portfolio_state: PortfolioState

    def __post_init__(self) -> None:
        if not isinstance(self.previous_portfolio_state, PortfolioState):
            raise PostMaterializationEconomicConsequenceDomainError(
                "A consequence requires one previous PortfolioState."
            )
        if not isinstance(self.source_materializations, tuple):
            raise PostMaterializationEconomicConsequenceDomainError(
                "Consequence provenance must be an immutable tuple."
            )
        if not self.source_materializations or not all(
            isinstance(source, OperationalMaterialization)
            for source in self.source_materializations
        ):
            raise PostMaterializationEconomicConsequenceDomainError(
                "A consequence requires one or more recognized materializations."
            )
        if not isinstance(self.resulting_portfolio_state, PortfolioState):
            raise PostMaterializationEconomicConsequenceDomainError(
                "A consequence requires one resulting PortfolioState."
            )
        if self.resulting_portfolio_state != _derive_state(
            self.previous_portfolio_state, self.source_materializations
        ):
            raise PostMaterializationEconomicConsequenceDomainError(
                "The resulting state must be the exact economic consequence of its sources."
            )


def derive_post_materialization_consequence(
    previous_portfolio_state: PortfolioState,
    materializations: Iterable[OperationalMaterialization],
) -> PostMaterializationEconomicConsequence:
    """Derive and publish the complete S0 + M* -> S1 causal relation."""
    if not isinstance(previous_portfolio_state, PortfolioState):
        raise PostMaterializationEconomicConsequenceDomainError(
            "Derivation requires one previous PortfolioState."
        )
    try:
        sources = tuple(materializations)
    except (TypeError, RuntimeError) as error:
        raise PostMaterializationEconomicConsequenceDomainError(
            "Derivation requires one or more recognized materializations."
        ) from error
    if not sources or not all(
        isinstance(source, OperationalMaterialization) for source in sources
    ):
        raise PostMaterializationEconomicConsequenceDomainError(
            "Derivation requires one or more recognized materializations."
        )

    return PostMaterializationEconomicConsequence(
        previous_portfolio_state=previous_portfolio_state,
        source_materializations=sources,
        resulting_portfolio_state=_derive_state(previous_portfolio_state, sources),
    )
