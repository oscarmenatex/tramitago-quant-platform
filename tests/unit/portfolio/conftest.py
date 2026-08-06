from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.decision_model import DecisionProposal
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.risk import RiskEvaluationOutcome, RiskEvaluationResult
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", PublicPublication(publication_id))
    return result


@pytest.fixture
def instrument() -> InstrumentReference:
    return InstrumentReference("FIGI", "BBG000B9XRY4")


@pytest.fixture
def currency() -> CurrencyReference:
    return CurrencyReference("USD")


@pytest.fixture
def proposal() -> DecisionProposal:
    return DecisionProposal.from_resolutions(
        "maintain exposure", (resolution("portfolio-evidence"),)
    )


@pytest.fixture
def current_state(instrument: InstrumentReference) -> PortfolioState:
    return PortfolioState((PortfolioPosition(instrument, Decimal("1")),))


@pytest.fixture
def accepted(proposal: DecisionProposal) -> RiskEvaluationResult:
    return RiskEvaluationResult(proposal, RiskEvaluationOutcome.ACCEPTED, "risk-v1")
