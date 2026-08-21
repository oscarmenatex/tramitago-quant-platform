from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import inspect

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import (
    ExecutionDomainError,
    InvestmentOperation,
    OperationDirection,
    ReconciliationReferenceTime,
    RequiredReconciliationScope,
    declare_required_reconciliation_scope,
    prepare_operational_request,
)
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioState


UTC_TIME = datetime(2026, 8, 21, 16, tzinfo=timezone.utc)


@pytest.fixture
def instrument() -> InstrumentReference:
    return InstrumentReference("ticker", "AAPL")


def _submission(target: PortfolioState) -> OperationalSubmission:
    return OperationalSubmission(prepare_operational_request(target))


def _operation(
    instrument: InstrumentReference,
    direction: OperationDirection = OperationDirection.BUY,
    quantity: Decimal = Decimal("1"),
) -> InvestmentOperation:
    return InvestmentOperation(instrument, direction, quantity)


def test_reference_time_requires_aware_datetime_with_determinable_offset() -> None:
    for invalid in (object(), datetime(2026, 8, 21, 16)):
        with pytest.raises(ExecutionDomainError):
            ReconciliationReferenceTime(invalid)  # type: ignore[arg-type]


def test_reference_time_uses_instant_equivalence() -> None:
    utc = ReconciliationReferenceTime(UTC_TIME)
    eastern = ReconciliationReferenceTime(
        datetime(2026, 8, 21, 12, tzinfo=timezone(timedelta(hours=-4)))
    )
    later = ReconciliationReferenceTime(UTC_TIME + timedelta(microseconds=1))
    assert utc == eastern
    assert hash(utc) == hash(eastern)
    assert utc != later


def test_empty_scope_is_valid_and_all_dimensions_are_explicit() -> None:
    scope = declare_required_reconciliation_scope(ReconciliationReferenceTime(UTC_TIME))
    assert scope.required_positions == ()
    assert scope.required_monetary_balances == ()
    assert scope.required_orders == ()
    assert scope.required_executions == ()


def test_order_membership_uses_instance_identity(target: PortfolioState) -> None:
    first = _submission(target)
    second = _submission(target)
    assert first == second and first is not second
    repeated = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(UTC_TIME), required_orders=(first, first)
    )
    distinct = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(UTC_TIME), required_orders=(first, second)
    )
    only_first = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(UTC_TIME), required_orders=(first,)
    )
    assert repeated.required_orders == (first,)
    assert len(distinct.required_orders) == 2
    assert repeated == only_first
    assert distinct != only_first


def test_execution_membership_uses_contractual_equality(
    instrument: InstrumentReference,
) -> None:
    same = _operation(instrument)
    equal = _operation(instrument)
    different_direction = _operation(instrument, OperationDirection.SELL)
    different_quantity = _operation(instrument, quantity=Decimal("2"))
    different_instrument = _operation(InstrumentReference("ticker", "MSFT"))
    scope = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(UTC_TIME),
        required_executions=(
            same,
            equal,
            different_direction,
            different_quantity,
            different_instrument,
        ),
    )
    assert len(scope.required_executions) == 4
    assert set(scope.required_executions) == {
        same,
        different_direction,
        different_quantity,
        different_instrument,
    }


def test_membership_order_and_duplicates_do_not_change_scope_meaning(
    target: PortfolioState, instrument: InstrumentReference
) -> None:
    other_instrument = InstrumentReference("ticker", "MSFT")
    usd = CurrencyReference("USD")
    eur = CurrencyReference("EUR")
    first_order = _submission(target)
    second_order = _submission(target)
    first_execution = _operation(instrument)
    second_execution = _operation(other_instrument)
    reference_time = ReconciliationReferenceTime(UTC_TIME)
    first = declare_required_reconciliation_scope(
        reference_time,
        (instrument, other_instrument, instrument),
        (usd, eur, usd),
        (first_order, second_order, first_order),
        (first_execution, second_execution, first_execution),
    )
    second = declare_required_reconciliation_scope(
        reference_time,
        (other_instrument, instrument),
        (eur, usd),
        (second_order, first_order),
        (second_execution, first_execution),
    )
    assert first == second
    assert hash(first) == hash(second)
    assert first.required_positions == second.required_positions
    assert first.required_monetary_balances == second.required_monetary_balances
    assert first.required_orders == second.required_orders
    assert first.required_executions == second.required_executions


@pytest.mark.parametrize(
    "keyword",
    (
        "required_positions",
        "required_monetary_balances",
        "required_orders",
        "required_executions",
    ),
)
def test_wrong_element_type_is_a_domain_error(keyword: str) -> None:
    with pytest.raises(ExecutionDomainError):
        declare_required_reconciliation_scope(
            ReconciliationReferenceTime(UTC_TIME), **{keyword: (object(),)}
        )


def test_inputs_are_snapshotted_and_result_is_immutable(
    instrument: InstrumentReference,
) -> None:
    positions = [instrument]
    scope = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(UTC_TIME), required_positions=positions
    )
    positions.append(InstrumentReference("ticker", "MSFT"))
    assert scope.required_positions == (instrument,)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        scope.required_positions = ()  # type: ignore[misc]


def test_construction_is_controlled_and_public_shape_is_exact() -> None:
    with pytest.raises(ExecutionDomainError):
        RequiredReconciliationScope()
    assert [field.name for field in fields(ReconciliationReferenceTime)] == ["value"]
    assert [field.name for field in fields(RequiredReconciliationScope)] == [
        "reference_time",
        "required_positions",
        "required_monetary_balances",
        "required_orders",
        "required_executions",
    ]
    assert tuple(
        inspect.signature(declare_required_reconciliation_scope).parameters
    ) == (
        "reference_time",
        "required_positions",
        "required_monetary_balances",
        "required_orders",
        "required_executions",
    )
    assert all(
        parameter.default == ()
        for parameter in tuple(
            inspect.signature(declare_required_reconciliation_scope).parameters.values()
        )[1:]
    )


def test_scope_does_not_publish_forbidden_responsibilities() -> None:
    forbidden = {
        "authority",
        "issuer",
        "scope_id",
        "policy_id",
        "status",
        "verification",
        "outcome",
        "coverage",
        "reconciled",
        "diagnosis",
        "resolution",
    }
    assert forbidden.isdisjoint(RequiredReconciliationScope.__annotations__)
