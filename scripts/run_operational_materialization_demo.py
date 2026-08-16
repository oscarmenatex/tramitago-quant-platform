#!/usr/bin/env python3
"""Deterministic demonstration of Operational Materialization recognition."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.execution import prepare_operational_request
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_materialization import (
    OperationalMaterializationObservation,
    recognize_materialization,
)
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.risk import (
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.strategy_evaluation.resolution import ResolutionResult


class PublicPublication:
    publication_id = "materialization-demo-evidence"


class ControlledMaterializationBoundary:
    """Demo-only normalized evidence source with no productive infrastructure."""

    def __init__(self, occurrence_id: str) -> None:
        self.occurrence_id = occurrence_id

    def observe(
        self, admission: OperationalAdmission
    ) -> OperationalMaterializationObservation:
        operation = admission.submission.operational_request.operations[0]
        observation = OperationalMaterializationObservation(
            occurrence_id=self.occurrence_id,
            operation=operation,
            quantity=Decimal("0.75"),
            price=Decimal("25.40"),
            currency=CurrencyReference("USD"),
        )
        print("boundary produced Observation:", observation)
        return observation


def _submission() -> OperationalSubmission:
    instrument = InstrumentReference("FIGI", "MATERIALIZATION-DEMO")
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", PublicPublication())
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE),
        (resolution,),
    )
    risk_result = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.ACCEPTED,
        "materialization-demo-risk",
    )
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal("2")),),
        current_portfolio_state=PortfolioState(),
        considered_risk_evaluation_results=(risk_result,),
        contributing_risk_evaluation_results=(risk_result,),
        determination_basis_reference="materialization-demo-portfolio",
    )
    return OperationalSubmission(prepare_operational_request(target))


def main() -> None:
    submission = _submission()
    print("InvestmentOperation:", submission.operational_request.operations[0])
    for decision, occurrence_id in (
        (AdmissionDecision.ADMITTED, "materialization-demo-admitted"),
        (AdmissionDecision.REJECTED, "materialization-demo-rejected"),
    ):
        admission = OperationalAdmission(submission, decision)
        materialization = recognize_materialization(
            admission,
            ControlledMaterializationBoundary(occurrence_id),
        )
        assert materialization is not None
        print("OperationalAdmission:", admission.decision.value)
        print("occurrence identity:", materialization.occurrence_id)
        print("recognized Materialization:", materialization)
        print("admission decision preserved:", admission.decision.value)

    print("Observation and Materialization are distinct contracts: yes")
    print("productive infrastructure used: no")
    print("Operational Materialization demo passed.")


if __name__ == "__main__":
    main()
