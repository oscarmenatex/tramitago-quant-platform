from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.decision_model import DecisionProposal
from quant_platform.portfolio import (
    DuplicatePortfolioComponentError, InvalidPortfolioComponentError,
    InvalidPortfolioTraceabilityError, MonetaryBalance, PortfolioPosition, PortfolioState,
)
from quant_platform.risk import RiskEvaluationOutcome, RiskEvaluationResult
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", PublicPublication(publication_id))
    return result


def main() -> None:
    a = InstrumentReference("FIGI", "A")
    b = InstrumentReference("FIGI", "B")
    usd = CurrencyReference("USD")
    positions = (PortfolioPosition(b, Decimal("2")), PortfolioPosition(a, Decimal("1")))
    cash = (MonetaryBalance(usd, Decimal("100")),)
    positions_only = PortfolioState(positions)
    cash_only = PortfolioState(monetary_balances=cash)
    mixed = PortfolioState(positions, cash)
    equivalent = PortfolioState(tuple(reversed(positions)), cash)
    assert mixed == equivalent and mixed.semantic_identity == equivalent.semantic_identity
    assert mixed != PortfolioState((PortfolioPosition(a, Decimal("3")),), cash)

    proposal = DecisionProposal.from_resolutions(
        "target state", (resolution("portfolio-demo"),)
    )
    conditional = RiskEvaluationResult(proposal, RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED, "risk-v1", ("hedge",))
    target = PortfolioState(positions, cash, decision_proposal=proposal, risk_evaluation_result=conditional, current_portfolio_state=positions_only)
    assert target.decision_proposal is proposal and target.risk_evaluation_result is conditional

    for action, error in (
        (lambda: PortfolioState(), InvalidPortfolioComponentError),
        (lambda: PortfolioState((PortfolioPosition(a, Decimal("1")), PortfolioPosition(a, Decimal("2")))), DuplicatePortfolioComponentError),
        (lambda: PortfolioState(positions, decision_proposal=proposal, risk_evaluation_result=RiskEvaluationResult(proposal, RiskEvaluationOutcome.REJECTED, "risk-v1"), current_portfolio_state=positions_only), InvalidPortfolioTraceabilityError),
    ):
        try:
            action()
        except error:
            pass
        else:
            raise AssertionError(f"Expected {error.__name__}")
    print("Portfolio State demo passed.")
    print(positions_only, cash_only, mixed, target.semantic_identity, sep="\n")


if __name__ == "__main__":
    main()
