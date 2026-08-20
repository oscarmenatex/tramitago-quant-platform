from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    ExternalExecutionAuthority,
    ExternalExecutionReality,
    InvestmentOperation,
    OperationDirection,
    ReportedExecution,
    SupportingExecutionEvidence,
    qualify_external_execution_reality,
)


UTC_TIME = datetime(2026, 8, 19, 15, 30, tzinfo=timezone.utc)


@pytest.fixture
def operation() -> InvestmentOperation:
    return InvestmentOperation(
        InstrumentReference("FIGI", "BBG000B9XRY4"),
        OperationDirection.BUY,
        Decimal("10"),
    )


def execution(
    execution_id: str = "broker-execution-1",
    *,
    quantity: Decimal = Decimal("2.5"),
    price: Decimal = Decimal("101.25"),
    currency: CurrencyReference | None = None,
) -> ReportedExecution:
    return ReportedExecution(
        execution_id,
        quantity,
        price,
        currency or CurrencyReference("USD"),
    )


def evidence(
    operation: InvestmentOperation,
    executions: tuple[ReportedExecution, ...] = (),
    *,
    authority: ExternalExecutionAuthority | None = None,
    reference_time: ExecutionRealityReferenceTime | None = None,
    observed_at_utc: datetime = UTC_TIME,
) -> SupportingExecutionEvidence:
    return SupportingExecutionEvidence(
        authority or ExternalExecutionAuthority("broker-authority"),
        reference_time or ExecutionRealityReferenceTime(UTC_TIME),
        observed_at_utc,
        operation,
        executions,
    )


@pytest.mark.parametrize("executions", [(), (execution(),), (execution(), execution("e2"))])
def test_qualifies_zero_one_or_many_reported_executions(
    operation: InvestmentOperation,
    executions: tuple[ReportedExecution, ...],
) -> None:
    source = evidence(operation, executions)

    reality = qualify_external_execution_reality((source,))

    assert reality.authority is source.authority
    assert reality.reference_time is source.reference_time
    assert reality.operation is operation
    assert reality.reported_executions is executions
    assert reality.supporting_evidence == (source,)


def test_compatible_evidence_preserves_all_provenance_by_identity(
    operation: InvestmentOperation,
) -> None:
    authority = ExternalExecutionAuthority("broker-authority")
    reference_time = ExecutionRealityReferenceTime(UTC_TIME)
    executions = (execution(), execution("broker-execution-2"))
    first = evidence(
        operation,
        executions,
        authority=authority,
        reference_time=reference_time,
    )
    second = evidence(
        operation,
        tuple(reversed(executions)),
        authority=authority,
        reference_time=ExecutionRealityReferenceTime(
            UTC_TIME.astimezone(timezone(timedelta(hours=-4)))
        ),
        observed_at_utc=UTC_TIME + timedelta(minutes=5),
    )

    reality = qualify_external_execution_reality(item for item in (first, second))

    assert len(reality.supporting_evidence) == 2
    assert reality.supporting_evidence[0] is first
    assert reality.supporting_evidence[1] is second


@pytest.mark.parametrize("difference", ["authority", "operation", "reference_time"])
def test_rejects_evidence_with_incompatible_scope(
    operation: InvestmentOperation,
    difference: str,
) -> None:
    first = evidence(operation, (execution(),))
    kwargs: dict[str, object] = {
        "authority": first.authority,
        "reference_time": first.reference_time,
    }
    other_operation = operation
    if difference == "authority":
        kwargs["authority"] = ExternalExecutionAuthority("another-authority")
    elif difference == "operation":
        other_operation = InvestmentOperation(
            InstrumentReference("FIGI", "DIFFERENT"),
            OperationDirection.BUY,
            Decimal("10"),
        )
    else:
        kwargs["reference_time"] = ExecutionRealityReferenceTime(
            UTC_TIME + timedelta(seconds=1)
        )
    second = evidence(other_operation, (execution(),), **kwargs)

    with pytest.raises(ExecutionDomainError):
        qualify_external_execution_reality((first, second))


@pytest.mark.parametrize(
    "second_executions",
    [
        (execution("different-id"),),
        (execution(quantity=Decimal("3")),),
        (execution(price=Decimal("99")),),
        (execution(currency=CurrencyReference("EUR")),),
    ],
)
def test_rejects_incompatible_complete_snapshots(
    operation: InvestmentOperation,
    second_executions: tuple[ReportedExecution, ...],
) -> None:
    first = evidence(operation, (execution(),))
    second = evidence(
        operation,
        second_executions,
        authority=first.authority,
        reference_time=first.reference_time,
    )

    with pytest.raises(ExecutionDomainError):
        qualify_external_execution_reality((first, second))


def test_economically_identical_executions_with_distinct_ids_remain_distinct(
    operation: InvestmentOperation,
) -> None:
    executions = (execution("one"), execution("two"))

    reality = qualify_external_execution_reality((evidence(operation, executions),))

    assert {item.external_execution_id for item in reality.reported_executions} == {
        "one",
        "two",
    }


def test_rejects_repeated_external_identity_even_when_facts_match(
    operation: InvestmentOperation,
) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(operation, (execution("same"), execution("same")))


@pytest.mark.parametrize("value", ["", "   ", None, 1])
def test_rejects_invalid_authority(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalExecutionAuthority(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", ["", "   ", None, 1])
def test_rejects_invalid_external_execution_id(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        execution(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "quantity",
    [1, Decimal("NaN"), Decimal("Infinity"), Decimal("0"), Decimal("-1")],
)
def test_rejects_invalid_quantity(quantity: object) -> None:
    with pytest.raises(ExecutionDomainError):
        execution(quantity=quantity)  # type: ignore[arg-type]


@pytest.mark.parametrize("price", [1, Decimal("NaN"), Decimal("Infinity")])
def test_rejects_invalid_price(price: object) -> None:
    with pytest.raises(ExecutionDomainError):
        execution(price=price)  # type: ignore[arg-type]


def test_rejects_invalid_currency() -> None:
    with pytest.raises(ExecutionDomainError):
        ReportedExecution("id", Decimal("1"), Decimal("2"), "USD")  # type: ignore[arg-type]


def test_rejects_naive_or_indeterminate_reference_time() -> None:
    with pytest.raises(ExecutionDomainError):
        ExecutionRealityReferenceTime(datetime(2026, 8, 19))


@pytest.mark.parametrize(
    "observed_at",
    [
        datetime(2026, 8, 19),
        datetime(2026, 8, 19, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_rejects_non_utc_observation_time(
    operation: InvestmentOperation,
    observed_at: datetime,
) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(operation, observed_at_utc=observed_at)


def test_rejects_invalid_operation(operation: InvestmentOperation) -> None:
    with pytest.raises(ExecutionDomainError):
        SupportingExecutionEvidence(
            ExternalExecutionAuthority("authority"),
            ExecutionRealityReferenceTime(UTC_TIME),
            UTC_TIME,
            object(),  # type: ignore[arg-type]
            (),
        )


def test_requires_at_least_one_supporting_evidence() -> None:
    with pytest.raises(ExecutionDomainError):
        qualify_external_execution_reality(())


def test_contracts_are_immutable_and_reality_cannot_be_directly_constructed(
    operation: InvestmentOperation,
) -> None:
    source = evidence(operation)
    reality = qualify_external_execution_reality((source,))

    with pytest.raises(FrozenInstanceError):
        reality.operation = operation  # type: ignore[misc]
    with pytest.raises(ExecutionDomainError):
        ExternalExecutionReality()


def test_public_contract_fields_are_exact() -> None:
    assert [field.name for field in fields(ExternalExecutionAuthority)] == ["value"]
    assert [field.name for field in fields(ExecutionRealityReferenceTime)] == ["value"]
    assert [field.name for field in fields(ReportedExecution)] == [
        "external_execution_id",
        "quantity",
        "price",
        "currency",
    ]
    assert [field.name for field in fields(SupportingExecutionEvidence)] == [
        "authority",
        "reference_time",
        "observed_at_utc",
        "operation",
        "reported_executions",
    ]
    assert [field.name for field in fields(ExternalExecutionReality)] == [
        "authority",
        "reference_time",
        "operation",
        "reported_executions",
        "supporting_evidence",
    ]
