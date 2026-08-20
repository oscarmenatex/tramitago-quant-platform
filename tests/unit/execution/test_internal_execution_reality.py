from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    InternalExecutionAuthority,
    InternalExecutionReality,
    InvestmentOperation,
    OperationDirection,
    SupportingInternalExecutionEvidence,
    qualify_internal_execution_reality,
)
from quant_platform.operational_materialization import OperationalMaterialization


UTC_TIME = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def operation() -> InvestmentOperation:
    return InvestmentOperation(
        InstrumentReference("FIGI", "BBG000B9XRY4"),
        OperationDirection.BUY,
        Decimal("10"),
    )


def materialization(
    operation: InvestmentOperation,
    occurrence_id: str = "occurrence-1",
    *,
    quantity: Decimal = Decimal("2.5"),
    price: Decimal = Decimal("101.25"),
    currency: CurrencyReference | None = None,
) -> OperationalMaterialization:
    return OperationalMaterialization(
        occurrence_id,
        operation,
        quantity,
        price,
        currency or CurrencyReference("USD"),
    )


def evidence(
    operation: InvestmentOperation,
    materializations: tuple[OperationalMaterialization, ...] = (),
    *,
    authority: InternalExecutionAuthority | None = None,
    reference_time: ExecutionRealityReferenceTime | None = None,
    observed_at_utc: datetime = UTC_TIME,
) -> SupportingInternalExecutionEvidence:
    return SupportingInternalExecutionEvidence(
        authority or InternalExecutionAuthority("execution-ledger"),
        reference_time or ExecutionRealityReferenceTime(UTC_TIME),
        observed_at_utc,
        operation,
        materializations,
    )


@pytest.mark.parametrize("count", [0, 1, 3])
def test_qualifies_zero_one_or_many_materializations(
    operation: InvestmentOperation,
    count: int,
) -> None:
    materializations = tuple(
        materialization(operation, f"occurrence-{index}") for index in range(count)
    )
    source = evidence(operation, materializations)

    reality = qualify_internal_execution_reality((source,))

    assert reality.reference_time is source.reference_time
    assert reality.operation is operation
    assert reality.materializations is materializations
    assert reality.supporting_evidence == (source,)


def test_compatible_evidence_preserves_all_provenance_and_original_facts(
    operation: InvestmentOperation,
) -> None:
    materializations = (
        materialization(operation, "occurrence-1"),
        materialization(operation, "occurrence-2"),
    )
    first = evidence(operation, materializations)
    second = evidence(
        operation,
        tuple(reversed(materializations)),
        authority=InternalExecutionAuthority("execution-journal"),
        reference_time=ExecutionRealityReferenceTime(
            UTC_TIME.astimezone(timezone(timedelta(hours=-4)))
        ),
        observed_at_utc=UTC_TIME + timedelta(minutes=10),
    )

    reality = qualify_internal_execution_reality(item for item in (first, second))

    assert reality.supporting_evidence[0] is first
    assert reality.supporting_evidence[1] is second
    assert reality.materializations[0] is materializations[0]
    assert reality.materializations[1] is materializations[1]


def test_distinct_authorities_can_corroborate_the_same_reality(
    operation: InvestmentOperation,
) -> None:
    fact = materialization(operation)
    first = evidence(
        operation,
        (fact,),
        authority=InternalExecutionAuthority("ledger"),
    )
    second = evidence(
        operation,
        (fact,),
        authority=InternalExecutionAuthority("journal"),
        reference_time=first.reference_time,
    )

    reality = qualify_internal_execution_reality((first, second))

    assert tuple(item.authority.value for item in reality.supporting_evidence) == (
        "ledger",
        "journal",
    )


def test_rejects_evidence_with_different_operation(
    operation: InvestmentOperation,
) -> None:
    first = evidence(operation)
    other_operation = InvestmentOperation(
        InstrumentReference("FIGI", "DIFFERENT"),
        OperationDirection.BUY,
        Decimal("10"),
    )
    second = evidence(
        other_operation,
        reference_time=first.reference_time,
    )

    with pytest.raises(ExecutionDomainError):
        qualify_internal_execution_reality((first, second))


def test_rejects_evidence_with_different_reference_time(
    operation: InvestmentOperation,
) -> None:
    first = evidence(operation)
    second = evidence(
        operation,
        reference_time=ExecutionRealityReferenceTime(UTC_TIME + timedelta(seconds=1)),
    )

    with pytest.raises(ExecutionDomainError):
        qualify_internal_execution_reality((first, second))


@pytest.mark.parametrize("difference", ["identity", "quantity", "price", "currency"])
def test_rejects_incompatible_complete_snapshots(
    operation: InvestmentOperation,
    difference: str,
) -> None:
    first = evidence(operation, (materialization(operation),))
    kwargs: dict[str, object] = {}
    occurrence_id = "occurrence-1"
    if difference == "identity":
        occurrence_id = "different-occurrence"
    elif difference == "quantity":
        kwargs["quantity"] = Decimal("3")
    elif difference == "price":
        kwargs["price"] = Decimal("99")
    else:
        kwargs["currency"] = CurrencyReference("EUR")
    second = evidence(
        operation,
        (materialization(operation, occurrence_id, **kwargs),),
        reference_time=first.reference_time,
    )

    with pytest.raises(ExecutionDomainError):
        qualify_internal_execution_reality((first, second))


def test_materialization_order_does_not_affect_snapshot_compatibility(
    operation: InvestmentOperation,
) -> None:
    facts = (
        materialization(operation, "one"),
        materialization(operation, "two"),
    )
    first = evidence(operation, facts)
    second = evidence(
        operation,
        tuple(reversed(facts)),
        reference_time=first.reference_time,
    )

    reality = qualify_internal_execution_reality((first, second))

    assert len(reality.materializations) == 2


def test_equal_economics_with_distinct_occurrence_ids_remain_distinct(
    operation: InvestmentOperation,
) -> None:
    facts = (
        materialization(operation, "one"),
        materialization(operation, "two"),
    )

    reality = qualify_internal_execution_reality((evidence(operation, facts),))

    assert {item.occurrence_id for item in reality.materializations} == {"one", "two"}


def test_rejects_repeated_occurrence_id(operation: InvestmentOperation) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(
            operation,
            (
                materialization(operation, "same"),
                materialization(operation, "same"),
            ),
        )


def test_rejects_materialization_from_another_operation(
    operation: InvestmentOperation,
) -> None:
    other_operation = InvestmentOperation(
        InstrumentReference("FIGI", "DIFFERENT"),
        OperationDirection.BUY,
        Decimal("10"),
    )

    with pytest.raises(ExecutionDomainError):
        evidence(operation, (materialization(other_operation),))


def test_requires_at_least_one_evidence() -> None:
    with pytest.raises(ExecutionDomainError):
        qualify_internal_execution_reality(())


@pytest.mark.parametrize("value", ["", "   ", None, 1])
def test_rejects_invalid_authority(value: object) -> None:
    with pytest.raises(ExecutionDomainError):
        InternalExecutionAuthority(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "observed_at",
    [
        datetime(2026, 8, 20),
        datetime(2026, 8, 20, tzinfo=timezone(timedelta(hours=1))),
    ],
)
def test_rejects_invalid_observed_at_utc(
    operation: InvestmentOperation,
    observed_at: datetime,
) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(operation, observed_at_utc=observed_at)


def test_rejects_invalid_reference_time(operation: InvestmentOperation) -> None:
    with pytest.raises(ExecutionDomainError):
        SupportingInternalExecutionEvidence(
            InternalExecutionAuthority("ledger"),
            object(),  # type: ignore[arg-type]
            UTC_TIME,
            operation,
            (),
        )


def test_rejects_invalid_operation() -> None:
    with pytest.raises(ExecutionDomainError):
        SupportingInternalExecutionEvidence(
            InternalExecutionAuthority("ledger"),
            ExecutionRealityReferenceTime(UTC_TIME),
            UTC_TIME,
            object(),  # type: ignore[arg-type]
            (),
        )


def test_rejects_invalid_materialization_type(
    operation: InvestmentOperation,
) -> None:
    with pytest.raises(ExecutionDomainError):
        evidence(operation, (object(),))  # type: ignore[arg-type]


def test_contracts_are_immutable_and_reality_is_qualification_only(
    operation: InvestmentOperation,
) -> None:
    reality = qualify_internal_execution_reality((evidence(operation),))

    with pytest.raises(FrozenInstanceError):
        reality.operation = operation  # type: ignore[misc]
    with pytest.raises(ExecutionDomainError):
        InternalExecutionReality()


def test_public_contract_fields_are_exact() -> None:
    assert [field.name for field in fields(InternalExecutionAuthority)] == ["value"]
    assert [field.name for field in fields(SupportingInternalExecutionEvidence)] == [
        "authority",
        "reference_time",
        "observed_at_utc",
        "operation",
        "materializations",
    ]
    assert [field.name for field in fields(InternalExecutionReality)] == [
        "reference_time",
        "operation",
        "materializations",
        "supporting_evidence",
    ]
