from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.decision_model import (
    DecisionProposal,
    EconomicProposition,
    ExposureOrientation,
)
from quant_platform.execution import (
    ExecutionDomainError,
    InvestmentOperation,
    OperationalIntent,
    OperationDirection,
    prepare_operational_request,
)
from quant_platform.operational_request import OperationalRequest
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
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


def risk_result(instrument: InstrumentReference) -> RiskEvaluationResult:
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(
        resolution, "publication", PublicPublication("execution-evidence")
    )
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    return RiskEvaluationResult(proposal, RiskEvaluationOutcome.ACCEPTED, "risk-v1")


def _target(
    current_positions: tuple[PortfolioPosition, ...],
    target_positions: tuple[PortfolioPosition, ...],
    *,
    current_balances: tuple[MonetaryBalance, ...] = (),
    target_balances: tuple[MonetaryBalance, ...] = (),
) -> PortfolioState:
    instrument = (
        target_positions[0].instrument
        if target_positions
        else current_positions[0].instrument
    )
    result = risk_result(instrument)
    current = PortfolioState(current_positions, current_balances)
    return PortfolioState(
        target_positions,
        target_balances,
        current_portfolio_state=current,
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-v1",
    )


def test_current_to_target_increase_and_reduction(target: PortfolioState) -> None:
    intent = OperationalIntent(target)
    operations = {
        item.instrument.identification_value: item for item in intent.operations
    }
    assert intent.target_portfolio_state is target
    assert operations["BUY-ME"].direction is OperationDirection.BUY
    assert operations["BUY-ME"].quantity == Decimal("3")
    assert operations["SELL-ME"].direction is OperationDirection.SELL
    assert operations["SELL-ME"].quantity == Decimal("2")


@pytest.mark.parametrize(
    ("current_quantity", "target_quantity", "direction", "quantity"),
    [
        (None, "4", OperationDirection.BUY, "4"),
        (None, "-4", OperationDirection.SELL, "4"),
        ("5", "2", OperationDirection.SELL, "3"),
        ("5", None, OperationDirection.SELL, "5"),
        ("3", "-2", OperationDirection.SELL, "5"),
    ],
)
def test_position_scenarios(
    current_quantity, target_quantity, direction, quantity
) -> None:
    instrument = InstrumentReference("FIGI", "SCENARIO")
    current = (
        (PortfolioPosition(instrument, Decimal(current_quantity)),)
        if current_quantity is not None
        else ()
    )
    target = (
        (PortfolioPosition(instrument, Decimal(target_quantity)),)
        if target_quantity is not None
        else ()
    )
    operation = OperationalIntent(_target(current, target)).operations[0]
    assert operation.direction is direction
    assert operation.quantity == Decimal(quantity)


def test_multiple_instruments_are_deterministic() -> None:
    a = InstrumentReference("FIGI", "A")
    b = InstrumentReference("FIGI", "B")
    target = _target(
        (), (PortfolioPosition(b, Decimal("2")), PortfolioPosition(a, Decimal("1")))
    )
    first = OperationalIntent(target)
    second = OperationalIntent(target)
    assert first == second
    assert hash(first) == hash(second)
    assert first.semantic_identity == second.semantic_identity
    assert {operation.instrument for operation in first.operations} == {a, b}


def test_economically_equal_target_is_valid_no_op() -> None:
    instrument = InstrumentReference("FIGI", "NO-OP")
    position = PortfolioPosition(instrument, Decimal("2"))
    target = _target((position,), (position,))
    assert OperationalIntent(target).operations == ()
    assert prepare_operational_request(target).operations == ()


def test_request_preserves_target_risk_provenance(target: PortfolioState) -> None:
    request = prepare_operational_request(target)
    assert isinstance(request, OperationalRequest)
    assert request.operational_intent.target_portfolio_state is target
    assert request.operations == request.operational_intent.operations
    assert (
        request.operational_intent.target_portfolio_state.contributing_risk_evaluation_results
        == target.contributing_risk_evaluation_results
    )


def test_max_execution_size_is_preserved_without_fragmentation() -> None:
    instrument = InstrumentReference("FIGI", "LIMITED")
    resolution = object.__new__(ResolutionResult)
    object.__setattr__(resolution, "publication", PublicPublication("limited-evidence"))
    proposal = DecisionProposal.from_resolutions(
        EconomicProposition(instrument, ExposureOrientation.POSITIVE), (resolution,)
    )
    constraint = RiskConstraint(
        RiskConstraintKind.MAX_EXECUTION_SIZE, Decimal("2"), "units"
    )
    result = RiskEvaluationResult(
        proposal,
        RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED,
        "risk-limited",
        (constraint,),
    )
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal("10")),),
        current_portfolio_state=PortfolioState(),
        considered_risk_evaluation_results=(result,),
        contributing_risk_evaluation_results=(result,),
        determination_basis_reference="portfolio-v1",
    )
    request = prepare_operational_request(target)
    assert request.operations == (
        InvestmentOperation(instrument, OperationDirection.BUY, Decimal("10")),
    )
    traced = request.operational_intent.target_portfolio_state.contributing_risk_evaluation_results[
        0
    ]
    assert traced.constraints == (constraint,)


def test_autonomous_monetary_change_is_rejected() -> None:
    instrument = InstrumentReference("FIGI", "CASH-CONTEXT")
    currency = CurrencyReference("USD")
    position = PortfolioPosition(instrument, Decimal("1"))
    target = _target(
        (position,),
        (position,),
        current_balances=(MonetaryBalance(currency, Decimal("10")),),
        target_balances=(MonetaryBalance(currency, Decimal("20")),),
    )
    with pytest.raises(ExecutionDomainError, match="autonomous monetary"):
        prepare_operational_request(target)


@pytest.mark.parametrize("invalid", [None, object(), "target", PortfolioState()])
def test_rejects_invalid_or_unprovenanced_target(invalid: object) -> None:
    with pytest.raises(ExecutionDomainError):
        OperationalIntent(invalid)  # type: ignore[arg-type]


def test_target_current_intent_and_request_are_immutable(
    target: PortfolioState,
) -> None:
    current = target.current_portfolio_state
    request = prepare_operational_request(target)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        request.operational_intent.target_portfolio_state = PortfolioState()  # type: ignore[misc]
    assert request.operational_intent.target_portfolio_state is target
    assert target.current_portfolio_state is current


def test_public_fields_are_exact() -> None:
    assert [field.name for field in fields(OperationalIntent)] == [
        "target_portfolio_state",
        "operations",
        "semantic_identity",
    ]


@pytest.mark.parametrize(
    ("instrument", "direction", "quantity"),
    [
        ("FIGI:A", OperationDirection.BUY, Decimal("1")),
        (InstrumentReference("FIGI", "A"), "BUY", Decimal("1")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, Decimal("0")),
        (InstrumentReference("FIGI", "A"), OperationDirection.SELL, Decimal("-1")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, Decimal("NaN")),
        (InstrumentReference("FIGI", "A"), OperationDirection.BUY, 1),
    ],
)
def test_investment_operation_rejects_invalid_public_values(
    instrument, direction, quantity
) -> None:
    with pytest.raises(ExecutionDomainError):
        InvestmentOperation(instrument, direction, quantity)  # type: ignore[arg-type]
