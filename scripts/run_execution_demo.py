#!/usr/bin/env python3
"""Deterministic demonstration of Execution Operational Planning."""

from decimal import Decimal

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.execution import OperationDirection, prepare_operational_request
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.risk import (
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    def __init__(self, publication_id: str) -> None:
        self.publication_id = publication_id


def _risk(instrument: InstrumentReference) -> RiskEvaluationResult:
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", PublicPublication("execution-demo"))
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    return RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-demo-v1",
        (RiskConstraint(RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("2"), "units"),),
    )


def _target(
    current: PortfolioState, instrument: InstrumentReference, quantity: Decimal
) -> PortfolioState:
    result = _risk(instrument)
    positions = () if quantity.is_zero() else (PortfolioPosition(instrument, quantity),)
    return PortfolioState(
        positions,
        current_portfolio_state=current,
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-demo-v1",
    )


def main() -> None:
    instrument = InstrumentReference("FIGI", "PLAN-ME")
    current = PortfolioState()
    target = _target(current, instrument, Decimal("10"))
    request = prepare_operational_request(target)
    intent = request.operational_intent
    constraint = target.contributing_risk_evaluation_results[0].constraints[0]

    assert intent.target_portfolio_state is target
    assert request.operations == intent.operations
    assert len(request.operations) == 1
    assert request.operations[0].direction is OperationDirection.BUY
    assert request.operations[0].quantity == Decimal("10")
    assert constraint.kind is RiskConstraintKind.MAX_EXECUTION_SIZE
    assert constraint.limit == Decimal("2")

    no_op_target = _target(target, instrument, Decimal("10"))
    no_op_request = prepare_operational_request(no_op_target)
    assert no_op_request.operations == ()

    print("current:", current.semantic_identity)
    print("target:", target.semantic_identity)
    print("risk contributors:", len(target.contributing_risk_evaluation_results))
    print("MAX_EXECUTION_SIZE:", constraint.limit, constraint.unit)
    print(
        "operations:",
        [(op.direction.value, str(op.quantity)) for op in request.operations],
    )
    print("intent:", intent.semantic_identity)
    print("request operations:", len(request.operations))
    print("no-op operations:", len(no_op_request.operations))
    print("Execution Operational Planning demo passed.")


if __name__ == "__main__":
    main()
