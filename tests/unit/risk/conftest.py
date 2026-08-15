"""Public-contract fixtures for IT-031-001."""

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
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
        EconomicProposition(
            InstrumentReference("FIGI", "BBG000B9XRY4"),
            ExposureOrientation.POSITIVE,
        ),
        (resolution("public-evidence-a"),),
    )


@pytest.fixture
def other_proposal() -> DecisionProposal:
    return DecisionProposal.from_resolutions(
        EconomicProposition(
            InstrumentReference("FIGI", "BBG000B9XRY4"),
            ExposureOrientation.FLAT,
        ),
        (resolution("public-evidence-a"),),
    )
