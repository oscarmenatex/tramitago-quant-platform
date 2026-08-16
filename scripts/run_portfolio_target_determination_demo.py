"""IT-032-003 demo; the authority below is not an official allocation policy."""

from decimal import Decimal

from quant_platform.core import InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.portfolio import (
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


def result(value: str, conditional: bool = False) -> RiskEvaluationResult:
    resolved = object.__new__(ResolutionResult)
    object.__setattr__(resolved, "publication", Publication("evidence-" + value))
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(
            InstrumentReference("FIGI", value), ExposureOrientation.POSITIVE
        ),
        (resolved,),
    )
    constraints = (
        (RiskConstraint(RiskConstraintKind.MAX_SIZE, Decimal("10"), "SHARES"),)
        if conditional
        else ()
    )
    outcome = (
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED
        if conditional
        else RiskEvaluationOutcome.ACCEPTED
    )
    return RiskEvaluationResult(proposal, outcome, "risk-v1", constraints)


class DemonstrationAuthority:
    """Uses a pre-determined composition; not an allocation policy."""

    basis_reference = "demo-pre-determined-composition-v1"

    def __init__(self, contributor: RiskEvaluationResult) -> None:
        self.contributor = contributor

    def determine(self, current, candidates):
        instrument = self.contributor.decision_proposal.economic_proposition.instrument
        return (
            (PortfolioPosition(instrument, Decimal("5")),),
            current.monetary_balances,
            (self.contributor,),
        )

    def is_constraint_satisfied(self, constraint, target, result):
        return (
            constraint.kind is RiskConstraintKind.MAX_SIZE
            and constraint.unit == "SHARES"
            and target.positions[0].quantity <= constraint.limit
        )


def main() -> None:
    current = PortfolioState()
    candidates = (result("A", True), result("B"))
    authority = DemonstrationAuthority(candidates[0])
    target = determine_target_portfolio(current, candidates, authority)
    print("Current:", current)
    print("Candidates:", target.considered_risk_evaluation_results)
    print("Contributors:", target.contributing_risk_evaluation_results)
    print("basis_reference:", target.determination_basis_reference)
    print("Target:", target)
    print("semantic_identity:", target.semantic_identity)
    print("Execution asset produced: False")


if __name__ == "__main__":
    main()
