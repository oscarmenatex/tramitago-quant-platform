"""Public-contract fixtures for IT-031-001."""

import pytest

from quant_platform.decision_model import DecisionProposal
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def resolution(publication_id: str) -> ResolutionResult:
    result = object.__new__(ResolutionResult)
    object.__setattr__(result, "publication", PublicPublication(publication_id))
    return result


@pytest.fixture
def proposal() -> DecisionProposal:
    return DecisionProposal.from_resolutions(
        "maintain current exposure", (resolution("public-evidence-a"),)
    )


@pytest.fixture
def other_proposal() -> DecisionProposal:
    return DecisionProposal.from_resolutions(
        "reduce exposure", (resolution("public-evidence-a"),)
    )
