"""Normative evidence for IT-032-003."""

from decimal import Decimal

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.portfolio import (
    InvalidPortfolioTargetAuthorityError,
    InvalidPortfolioTargetCompositionError,
    InvalidPortfolioTargetInputError,
    PortfolioPosition,
    PortfolioState,
    determine_target_portfolio,
)
from quant_platform.risk import (
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class Publication:
    def __init__(self, value: str) -> None:
        self.publication_id = value


def candidate(
    value: str,
    orientation: ExposureOrientation = ExposureOrientation.POSITIVE,
    outcome: RiskEvaluationOutcome = RiskEvaluationOutcome.ACCEPTED,
    constraints=(),
) -> RiskEvaluationResult:
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", Publication("evidence-" + value))
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(InstrumentReference("FIGI", value), orientation),
        (resolution,),
    )
    return RiskEvaluationResult(proposal, outcome, "risk-v1", constraints)


class Authority:
    basis_reference = "demo-authority-v1"

    def __init__(self, positions=(), contributors=(), supported=True) -> None:
        self.positions = positions
        self.contributors = contributors
        self.supported = supported

    def determine(self, current, candidates):
        return self.positions, current.monetary_balances, self.contributors

    def is_constraint_satisfied(self, constraint, target, result):
        return self.supported


def test_accepted_candidate_produces_new_target_with_plural_provenance() -> None:
    result = candidate("A")
    current = PortfolioState()
    target = determine_target_portfolio(
        current,
        (result,),
        Authority(
            (
                PortfolioPosition(
                    result.decision_proposal.economic_proposition.instrument,
                    Decimal("2"),
                ),
            ),
            (result,),
        ),
    )
    assert target is not current
    assert target.considered_risk_evaluation_results == (result,)
    assert target.contributing_risk_evaluation_results == (result,)
    assert target.determination_basis_reference == "demo-authority-v1"


def test_multiple_candidates_allow_subset_and_order_is_non_semantic() -> None:
    a, b = candidate("A"), candidate("B")
    authority = Authority(
        (
            PortfolioPosition(
                a.decision_proposal.economic_proposition.instrument, Decimal("1")
            ),
        ),
        (a,),
    )
    first = determine_target_portfolio(PortfolioState(), (a, b), authority)
    second = determine_target_portfolio(PortfolioState(), (b, a), authority)
    assert first == second and first.semantic_identity == second.semantic_identity
    assert (
        first.considered_risk_evaluation_results
        == second.considered_risk_evaluation_results
    )


def test_zero_contributors_preserves_positions_and_returns_new_instance() -> None:
    result = candidate("A")
    current = PortfolioState(
        (
            PortfolioPosition(
                result.decision_proposal.economic_proposition.instrument, Decimal("1")
            ),
        )
    )
    target = determine_target_portfolio(
        current, (result,), Authority(current.positions, ())
    )
    assert target is not current and target == current and hash(target) == hash(current)


@pytest.mark.parametrize("bad", [None, object()])
def test_rejects_invalid_current_or_authority(bad) -> None:
    result = candidate("A")
    error = (
        InvalidPortfolioTargetInputError
        if bad is None
        else InvalidPortfolioTargetAuthorityError
    )
    with pytest.raises(error):
        determine_target_portfolio(
            bad if bad is None else PortfolioState(),
            (result,),
            Authority() if bad is None else bad,
        )


def test_rejects_empty_or_rejected_candidates() -> None:
    with pytest.raises(InvalidPortfolioTargetInputError):
        determine_target_portfolio(PortfolioState(), (), Authority())
    with pytest.raises(InvalidPortfolioTargetInputError):
        determine_target_portfolio(
            PortfolioState(),
            (candidate("A", outcome=RiskEvaluationOutcome.REJECTED),),
            Authority(),
        )


def test_rejects_external_or_duplicate_instrument_contributors() -> None:
    a, b = candidate("A"), candidate("B")
    with pytest.raises(InvalidPortfolioTargetCompositionError):
        determine_target_portfolio(PortfolioState(), (a,), Authority((), (b,)))
    duplicate = candidate("A", ExposureOrientation.FLAT)
    with pytest.raises(InvalidPortfolioTargetCompositionError):
        determine_target_portfolio(
            PortfolioState(), (a, duplicate), Authority((), (a, duplicate))
        )


@pytest.mark.parametrize(
    "orientation,quantity",
    [
        (ExposureOrientation.POSITIVE, Decimal("-1")),
        (ExposureOrientation.NEGATIVE, Decimal("1")),
    ],
)
def test_rejects_orientation_violation(orientation, quantity) -> None:
    result = candidate("A", orientation)
    position = PortfolioPosition(
        result.decision_proposal.economic_proposition.instrument, quantity
    )
    with pytest.raises(InvalidPortfolioTargetCompositionError):
        determine_target_portfolio(
            PortfolioState(), (result,), Authority((position,), (result,))
        )


def test_flat_requires_absent_position_and_can_produce_empty_target() -> None:
    result = candidate("A", ExposureOrientation.FLAT)
    current = PortfolioState(
        (
            PortfolioPosition(
                result.decision_proposal.economic_proposition.instrument, Decimal("1")
            ),
        )
    )
    target = determine_target_portfolio(current, (result,), Authority((), (result,)))
    assert target.positions == ()


def test_rejects_unattributed_change() -> None:
    result = candidate("A")
    other = InstrumentReference("FIGI", "B")
    with pytest.raises(InvalidPortfolioTargetCompositionError):
        determine_target_portfolio(
            PortfolioState(),
            (result,),
            Authority((PortfolioPosition(other, Decimal("1")),), (result,)),
        )


def test_supported_constraint_passes_and_unsupported_fails() -> None:
    constraint = RiskConstraint(RiskConstraintKind.MAX_SIZE, Decimal("5"), "SHARES")
    result = candidate(
        "A",
        outcome=RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(constraint,),
    )
    position = PortfolioPosition(
        result.decision_proposal.economic_proposition.instrument, Decimal("2")
    )
    determine_target_portfolio(
        PortfolioState(), (result,), Authority((position,), (result,), True)
    )
    with pytest.raises(InvalidPortfolioTargetCompositionError):
        determine_target_portfolio(
            PortfolioState(), (result,), Authority((position,), (result,), False)
        )


def test_execution_constraint_is_preserved_without_determining_position() -> None:
    constraint = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("5"), "SHARES"
    )
    result = candidate(
        "A",
        outcome=RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        constraints=(constraint,),
    )
    target = determine_target_portfolio(
        PortfolioState(), (result,), Authority((), (result,), False)
    )
    assert target.positions == ()
    assert target.contributing_risk_evaluation_results[0].constraints == (constraint,)
