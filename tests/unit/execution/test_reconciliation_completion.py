from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import (
    EconomicRealityDimension,
    EconomicRealityVerification,
    EconomicRealityVerificationOutcome as EconomicOutcome,
    EconomicRealityVerificationResult,
)
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    ExecutionRealityVerification,
    ExecutionRealityVerificationOutcome,
    InvestmentOperation,
    OperationDirection,
    OrderRealityReferenceTime,
    OrderRealityVerification,
    OrderRealityVerificationOutcome,
    ReconciliationCompletionCondition as Condition,
    ReconciliationCompletionQualification,
    ReconciliationReferenceTime,
    declare_required_reconciliation_scope,
    qualify_reconciliation_completion,
)
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityReferenceTime,
)
from quant_platform.operational_submission import OperationalSubmission


NOW = datetime(2026, 8, 21, 16, tzinfo=timezone.utc)
AAPL = InstrumentReference("FIGI", "AAPL")
MSFT = InstrumentReference("FIGI", "MSFT")
USD = CurrencyReference("USD")


def operation(identity: InstrumentReference = AAPL) -> InvestmentOperation:
    return InvestmentOperation(identity, OperationDirection.BUY, Decimal("1"))


def submission() -> OperationalSubmission:
    value = object.__new__(OperationalSubmission)
    object.__setattr__(value, "operational_request", object())
    return value


def scope(*, positions=(), balances=(), orders=(), executions=()):
    return declare_required_reconciliation_scope(
        ReconciliationReferenceTime(NOW), positions, balances, orders, executions
    )


def economic(*results, when=NOW):
    reference_time = InternalEconomicRealityReferenceTime(when)
    internal = SimpleNamespace(reference_time=reference_time)
    external = SimpleNamespace(reference_time=reference_time)
    return EconomicRealityVerification._create(
        internal,
        external,
        frozenset(
            result
            for result in results
            if result.dimension is EconomicRealityDimension.POSITION
        ),
        frozenset(
            result
            for result in results
            if result.dimension is EconomicRealityDimension.MONETARY_BALANCE
        ),
    )


def economic_result(dimension, identity, outcome):
    return EconomicRealityVerificationResult._create(
        dimension, identity, outcome, Decimal("1"), None
    )


def order_verification(
    source, outcome=OrderRealityVerificationOutcome.AGREEMENT, *, when=NOW
):
    reference_time = OrderRealityReferenceTime(when)
    reality = SimpleNamespace(submission=source, reference_time=reference_time)
    return OrderRealityVerification._create(reality, reality, outcome)


def execution_verification(
    source,
    outcome=ExecutionRealityVerificationOutcome.AGREEMENT,
    *,
    when=NOW,
):
    reference_time = ExecutionRealityReferenceTime(when)
    reality = SimpleNamespace(operation=source, reference_time=reference_time)
    return ExecutionRealityVerification._create(reality, reality, outcome)


@pytest.mark.parametrize(
    ("requirements", "result", "expected"),
    [
        (
            (AAPL,),
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
            ),
            Condition.RECONCILED,
        ),
        (
            (AAPL,),
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.NOT_COMPARABLE
            ),
            Condition.INSUFFICIENT_EVIDENCE,
        ),
        (
            (AAPL,),
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.DISCREPANCY
            ),
            Condition.DIVERGENT,
        ),
    ],
)
def test_economic_outcomes(requirements, result, expected) -> None:
    assert (
        qualify_reconciliation_completion(
            scope(positions=requirements), economic(result)
        ).condition
        is expected
    )


def test_empty_scope_is_reconciled_and_all_evidence_is_extraneous() -> None:
    order = order_verification(submission(), when=NOW + timedelta(days=1))
    execution = execution_verification(operation(), when=NOW + timedelta(days=1))
    result = qualify_reconciliation_completion(
        scope(), economic(when=NOW + timedelta(days=1)), (order,), (execution,)
    )
    assert result.condition is Condition.RECONCILED
    assert result.economic_verification is None
    assert result.order_verifications == ()
    assert result.execution_verifications == ()


@pytest.mark.parametrize(
    ("verification", "expected"),
    [
        (None, Condition.INSUFFICIENT_EVIDENCE),
        (OrderRealityVerificationOutcome.AGREEMENT, Condition.RECONCILED),
        (OrderRealityVerificationOutcome.DISCREPANCY, Condition.DIVERGENT),
    ],
)
def test_order_outcomes(verification, expected) -> None:
    source = submission()
    evidence = (
        () if verification is None else (order_verification(source, verification),)
    )
    assert (
        qualify_reconciliation_completion(
            scope(orders=(source,)), order_verifications=evidence
        ).condition
        is expected
    )


@pytest.mark.parametrize(
    ("verification", "expected"),
    [
        (None, Condition.INSUFFICIENT_EVIDENCE),
        (ExecutionRealityVerificationOutcome.AGREEMENT, Condition.RECONCILED),
        (ExecutionRealityVerificationOutcome.DISCREPANCY, Condition.DIVERGENT),
    ],
)
def test_execution_outcomes(verification, expected) -> None:
    source = operation()
    evidence = (
        () if verification is None else (execution_verification(source, verification),)
    )
    assert (
        qualify_reconciliation_completion(
            scope(executions=(source,)), execution_verifications=evidence
        ).condition
        is expected
    )


def test_mixed_agreement_and_divergence_precedence() -> None:
    order = submission()
    execution = operation()
    result = qualify_reconciliation_completion(
        scope(
            positions=(AAPL,), balances=(USD,), orders=(order,), executions=(execution,)
        ),
        economic(
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
            ),
            economic_result(
                EconomicRealityDimension.MONETARY_BALANCE,
                USD,
                EconomicOutcome.AGREEMENT,
            ),
        ),
        (order_verification(order),),
        (execution_verification(execution),),
    )
    assert result.condition is Condition.RECONCILED

    divergent = qualify_reconciliation_completion(
        scope(positions=(AAPL,), orders=(order,), executions=(execution,)),
        economic(
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.DISCREPANCY
            )
        ),
        execution_verifications=(execution_verification(execution),),
    )
    assert divergent.condition is Condition.DIVERGENT


def test_dimension_and_identity_mismatch_are_insufficient() -> None:
    wrong_dimension = economic_result(
        EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
    )
    wrong_identity = economic_result(
        EconomicRealityDimension.MONETARY_BALANCE,
        CurrencyReference("EUR"),
        EconomicOutcome.AGREEMENT,
    )
    assert (
        qualify_reconciliation_completion(
            scope(balances=(USD,)), economic(wrong_dimension, wrong_identity)
        ).condition
        is Condition.INSUFFICIENT_EVIDENCE
    )


def test_equivalent_offsets_are_compatible_for_all_used_evidence() -> None:
    eastern = NOW.astimezone(timezone(timedelta(hours=-4)))
    order = submission()
    execution = operation()
    result = qualify_reconciliation_completion(
        scope(positions=(AAPL,), orders=(order,), executions=(execution,)),
        economic(
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
            ),
            when=eastern,
        ),
        (order_verification(order, when=eastern),),
        (execution_verification(execution, when=eastern),),
    )
    assert result.condition is Condition.RECONCILED


@pytest.mark.parametrize("kind", ["economic", "order", "execution"])
def test_required_temporal_mismatch_is_domain_error(kind) -> None:
    later = NOW + timedelta(seconds=1)
    order = submission()
    execution = operation()
    kwargs = {}
    required = {}
    if kind == "economic":
        required["positions"] = (AAPL,)
        kwargs["economic_verification"] = economic(
            economic_result(
                EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
            ),
            when=later,
        )
    elif kind == "order":
        required["orders"] = (order,)
        kwargs["order_verifications"] = (order_verification(order, when=later),)
    else:
        required["executions"] = (execution,)
        kwargs["execution_verifications"] = (
            execution_verification(execution, when=later),
        )
    with pytest.raises(ExecutionDomainError):
        qualify_reconciliation_completion(scope(**required), **kwargs)


@pytest.mark.parametrize("kind", ["order", "execution"])
def test_duplicate_instance_is_one_evidence_but_distinct_collision_is_error(
    kind,
) -> None:
    if kind == "order":
        required = submission()
        first = order_verification(required)
        kwargs = {"order_verifications": (first, first)}
        required_scope = scope(orders=(required,))
        field = "order_verifications"
        second = order_verification(required)
    else:
        required = operation()
        first = execution_verification(required)
        kwargs = {"execution_verifications": (first, first)}
        required_scope = scope(executions=(required,))
        field = "execution_verifications"
        second = execution_verification(required)
    result = qualify_reconciliation_completion(required_scope, **kwargs)
    assert getattr(result, field) == (first,)
    kwargs[field] = (first, second)
    with pytest.raises(ExecutionDomainError):
        qualify_reconciliation_completion(required_scope, **kwargs)


def test_exact_used_provenance_excludes_extraneous_and_preserves_full_economic() -> (
    None
):
    required_order = submission()
    extra_order = submission()
    required_execution = operation(AAPL)
    extra_execution = operation(MSFT)
    used_order = order_verification(required_order)
    used_execution = execution_verification(required_execution)
    full_economic = economic(
        economic_result(
            EconomicRealityDimension.POSITION, AAPL, EconomicOutcome.AGREEMENT
        ),
        economic_result(
            EconomicRealityDimension.POSITION, MSFT, EconomicOutcome.DISCREPANCY
        ),
    )
    required_scope = scope(
        positions=(AAPL,), orders=(required_order,), executions=(required_execution,)
    )
    result = qualify_reconciliation_completion(
        required_scope,
        full_economic,
        (order_verification(extra_order, when=NOW + timedelta(days=1)), used_order),
        (
            execution_verification(extra_execution, when=NOW + timedelta(days=1)),
            used_execution,
        ),
    )
    assert result.required_scope is required_scope
    assert result.economic_verification is full_economic
    assert result.order_verifications == (used_order,)
    assert result.execution_verifications == (used_execution,)
    assert result.condition is Condition.RECONCILED


def test_contract_is_exact_controlled_immutable_and_snapshotted() -> None:
    assert tuple(Condition) == (
        Condition.RECONCILED,
        Condition.DIVERGENT,
        Condition.INSUFFICIENT_EVIDENCE,
    )
    assert [field.name for field in fields(ReconciliationCompletionQualification)] == [
        "required_scope",
        "economic_verification",
        "order_verifications",
        "execution_verifications",
        "condition",
    ]
    with pytest.raises(ExecutionDomainError):
        ReconciliationCompletionQualification(condition=Condition.DIVERGENT)
    source = submission()
    evidence = [order_verification(source)]
    result = qualify_reconciliation_completion(
        scope(orders=(source,)), order_verifications=evidence
    )
    evidence.append(order_verification(submission()))
    assert result.order_verifications == (evidence[0],)
    with pytest.raises((FrozenInstanceError, AttributeError)):
        result.condition = Condition.DIVERGENT


@pytest.mark.parametrize(
    "kwargs",
    [
        {"required_scope": object()},
        {"required_scope": scope(), "economic_verification": object()},
        {"required_scope": scope(), "order_verifications": (object(),)},
        {"required_scope": scope(), "execution_verifications": (object(),)},
    ],
)
def test_invalid_public_types_cross_execution_domain_error(kwargs) -> None:
    with pytest.raises(ExecutionDomainError):
        qualify_reconciliation_completion(**kwargs)
