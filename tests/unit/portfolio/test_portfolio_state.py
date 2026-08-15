from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import (
    DuplicatePortfolioComponentError,
    InvalidPortfolioComponentError,
    InvalidPortfolioTraceabilityError,
    MonetaryBalance,
    PortfolioPosition,
    PortfolioState,
)
from quant_platform.risk import (
    RiskConstraint,
    RiskConstraintKind,
    RiskEvaluationOutcome,
    RiskEvaluationResult,
)
from quant_platform.decision_model import EconomicProposition, ExposureOrientation


def test_valid_positions_only(instrument: InstrumentReference) -> None:
    assert PortfolioState((PortfolioPosition(instrument, Decimal("2")),)).positions


def test_valid_balances_only(currency: CurrencyReference) -> None:
    assert PortfolioState(
        monetary_balances=(MonetaryBalance(currency, Decimal("20")),)
    ).monetary_balances


def test_valid_mixed_state(
    instrument: InstrumentReference, currency: CurrencyReference
) -> None:
    state = PortfolioState(
        (PortfolioPosition(instrument, Decimal("2")),),
        (MonetaryBalance(currency, Decimal("20")),),
    )
    assert state.positions and state.monetary_balances


def test_accepts_empty_state_with_reproducible_identity() -> None:
    one = PortfolioState()
    two = PortfolioState((), ())

    assert one.positions == ()
    assert one.monetary_balances == ()
    assert one == two
    assert hash(one) == hash(two)
    assert one.semantic_identity == two.semantic_identity


def test_empty_state_is_immutable() -> None:
    state = PortfolioState()

    with pytest.raises((FrozenInstanceError, AttributeError)):
        state.positions = ()  # type: ignore[misc]


def test_empty_state_can_act_as_current(
    instrument: InstrumentReference, proposal, accepted
) -> None:
    current = PortfolioState()
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal("1")),),
        decision_proposal=proposal,
        risk_evaluation_result=accepted,
        current_portfolio_state=current,
    )

    assert target.current_portfolio_state is current


def test_empty_target_preserves_valid_traceability(
    proposal, accepted, current_state
) -> None:
    target = PortfolioState(
        decision_proposal=proposal,
        risk_evaluation_result=accepted,
        current_portfolio_state=current_state,
    )

    assert target.decision_proposal is proposal
    assert target.risk_evaluation_result is accepted
    assert target.current_portfolio_state is current_state


def test_empty_target_rejects_invalid_traceability(proposal, current_state) -> None:
    rejected = RiskEvaluationResult(proposal, RiskEvaluationOutcome.REJECTED, "risk-v1")

    with pytest.raises(InvalidPortfolioTraceabilityError):
        PortfolioState(
            decision_proposal=proposal,
            risk_evaluation_result=rejected,
            current_portfolio_state=current_state,
        )


@pytest.mark.parametrize(
    "value",
    [Decimal("0"), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), 1],
)
def test_rejects_invalid_position_quantity(
    instrument: InstrumentReference, value: object
) -> None:
    with pytest.raises(InvalidPortfolioComponentError):
        PortfolioPosition(instrument, value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [Decimal("0"), Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity"), 1],
)
def test_rejects_invalid_monetary_amount(
    currency: CurrencyReference, value: object
) -> None:
    with pytest.raises(InvalidPortfolioComponentError):
        MonetaryBalance(currency, value)  # type: ignore[arg-type]


def test_accepts_negative_quantity(instrument: InstrumentReference) -> None:
    assert PortfolioPosition(instrument, Decimal("-1")).quantity < 0


def test_accepts_negative_amount(currency: CurrencyReference) -> None:
    assert MonetaryBalance(currency, Decimal("-1")).amount < 0


def test_rejects_invalid_instrument_reference() -> None:
    with pytest.raises(InvalidPortfolioComponentError):
        PortfolioPosition("FIGI", Decimal("1"))  # type: ignore[arg-type]


def test_rejects_invalid_currency_reference() -> None:
    with pytest.raises(InvalidPortfolioComponentError):
        MonetaryBalance("USD", Decimal("1"))  # type: ignore[arg-type]


def test_rejects_duplicate_instrument(instrument: InstrumentReference) -> None:
    with pytest.raises(DuplicatePortfolioComponentError):
        PortfolioState(
            (
                PortfolioPosition(instrument, Decimal("1")),
                PortfolioPosition(instrument, Decimal("2")),
            )
        )


def test_rejects_duplicate_currency(currency: CurrencyReference) -> None:
    with pytest.raises(DuplicatePortfolioComponentError):
        PortfolioState(
            monetary_balances=(
                MonetaryBalance(currency, Decimal("1")),
                MonetaryBalance(currency, Decimal("2")),
            )
        )


def test_canonical_order_is_input_independent() -> None:
    first = PortfolioPosition(InstrumentReference("FIGI", "B"), Decimal("1"))
    second = PortfolioPosition(InstrumentReference("FIGI", "A"), Decimal("2"))
    assert (
        PortfolioState((first, second)).positions
        == PortfolioState((second, first)).positions
    )


def test_equivalent_states_are_equal_and_hash_equally(
    instrument: InstrumentReference,
) -> None:
    one = PortfolioState((PortfolioPosition(instrument, Decimal("1.0")),))
    two = PortfolioState((PortfolioPosition(instrument, Decimal("1.00")),))
    assert one == two
    assert hash(one) == hash(two)
    assert one.semantic_identity == two.semantic_identity


def test_identity_changes_with_instrument() -> None:
    one = PortfolioState(
        (PortfolioPosition(InstrumentReference("FIGI", "A"), Decimal("1")),)
    )
    two = PortfolioState(
        (PortfolioPosition(InstrumentReference("FIGI", "B"), Decimal("1")),)
    )
    assert one != two


def test_identity_changes_with_quantity(instrument: InstrumentReference) -> None:
    assert PortfolioState(
        (PortfolioPosition(instrument, Decimal("1")),)
    ) != PortfolioState((PortfolioPosition(instrument, Decimal("2")),))


def test_identity_changes_with_currency() -> None:
    one = PortfolioState(
        monetary_balances=(MonetaryBalance(CurrencyReference("USD"), Decimal("1")),)
    )
    two = PortfolioState(
        monetary_balances=(MonetaryBalance(CurrencyReference("EUR"), Decimal("1")),)
    )
    assert one != two


def test_identity_changes_with_amount(currency: CurrencyReference) -> None:
    assert PortfolioState(
        monetary_balances=(MonetaryBalance(currency, Decimal("1")),)
    ) != PortfolioState(monetary_balances=(MonetaryBalance(currency, Decimal("2")),))


def test_is_immutable(instrument: InstrumentReference) -> None:
    state = PortfolioState((PortfolioPosition(instrument, Decimal("1")),))
    with pytest.raises((FrozenInstanceError, AttributeError)):
        state.positions = ()  # type: ignore[misc]


def test_traceability_is_preserved_and_excluded_from_identity(
    instrument: InstrumentReference, proposal, accepted, current_state
) -> None:
    components = (PortfolioPosition(instrument, Decimal("2")),)
    traced = PortfolioState(
        components,
        decision_proposal=proposal,
        risk_evaluation_result=accepted,
        current_portfolio_state=current_state,
    )
    plain = PortfolioState(components)
    assert traced == plain and hash(traced) == hash(plain)
    assert traced.decision_proposal is proposal
    assert traced.risk_evaluation_result is accepted
    assert traced.current_portfolio_state is current_state


def test_rejects_incoherent_proposal(
    instrument, proposal, accepted, current_state
) -> None:
    other = object.__new__(type(proposal))
    object.__setattr__(
        other,
        "economic_proposition",
        EconomicProposition(
            proposal.economic_proposition.instrument,
            ExposureOrientation.NEGATIVE,
        ),
    )
    object.__setattr__(other, "evidence_references", proposal.evidence_references)
    object.__setattr__(other, "semantic_identity", "other")
    with pytest.raises(InvalidPortfolioTraceabilityError):
        PortfolioState(
            (PortfolioPosition(instrument, Decimal("2")),),
            decision_proposal=other,
            risk_evaluation_result=accepted,
            current_portfolio_state=current_state,
        )


def test_rejects_rejected_result(instrument, proposal, current_state) -> None:
    rejected = RiskEvaluationResult(proposal, RiskEvaluationOutcome.REJECTED, "risk-v1")
    with pytest.raises(InvalidPortfolioTraceabilityError):
        PortfolioState(
            (PortfolioPosition(instrument, Decimal("2")),),
            decision_proposal=proposal,
            risk_evaluation_result=rejected,
            current_portfolio_state=current_state,
        )


def test_accepts_conditionally_accepted_result(
    instrument, proposal, current_state
) -> None:
    constraint = RiskConstraint(
        RiskConstraintKind.MAX_EXPOSURE, Decimal("0.25"), "NAV_RATIO"
    )
    conditional = RiskEvaluationResult(
        proposal, RiskEvaluationOutcome.CONDITIONALLY_ACCEPTED, "risk-v1", (constraint,)
    )
    state = PortfolioState(
        (PortfolioPosition(instrument, Decimal("2")),),
        decision_proposal=proposal,
        risk_evaluation_result=conditional,
        current_portfolio_state=current_state,
    )
    assert state.risk_evaluation_result is conditional
    assert state.risk_evaluation_result.constraints == (constraint,)
