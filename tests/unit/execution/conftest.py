from decimal import Decimal

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.risk import RiskEvaluationOutcome, RiskEvaluationResult
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def risk_result(instrument: InstrumentReference) -> RiskEvaluationResult:
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(
        resolution, "publication", PublicPublication("execution-evidence")
    )
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    return RiskEvaluationResult(proposal, RiskEvaluationOutcome.ACCEPTED, "risk-v1")


@pytest.fixture
def target() -> PortfolioState:
    bought = InstrumentReference("FIGI", "BUY-ME")
    sold = InstrumentReference("FIGI", "SELL-ME")
    current = PortfolioState(
        (PortfolioPosition(bought, Decimal("1")), PortfolioPosition(sold, Decimal("5")))
    )
    result = risk_result(bought)
    return PortfolioState(
        (
            PortfolioPosition(bought, Decimal("4")),
            PortfolioPosition(sold, Decimal("3")),
        ),
        current_portfolio_state=current,
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-v1",
    )
