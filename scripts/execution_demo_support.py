"""Construction support for historical downstream demos during Execution migration."""

from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.portfolio import PortfolioState
from quant_platform.portfolio_transition import PortfolioTransition
from quant_platform.risk import RiskEvaluationOutcome, RiskEvaluationResult
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def target_from_transition(transition: PortfolioTransition) -> PortfolioState:
    instrument = transition.position_transitions[0].instrument
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", PublicPublication("demo-evidence"))
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    result = RiskEvaluationResult(proposal, RiskEvaluationOutcome.ACCEPTED, "risk-v1")
    target = transition.target_portfolio_state
    return PortfolioState(
        target.positions,
        target.monetary_balances,
        current_portfolio_state=transition.current_portfolio_state,
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-v1",
    )
