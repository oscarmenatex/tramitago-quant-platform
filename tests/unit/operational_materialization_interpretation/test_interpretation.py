from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretation,
    OperationalMaterializationInterpretationDomainError,
    interpret_materializations,
)


def test_one_materialization_produces_its_exact_quantity(
    operation: InvestmentOperation, materialization_factory
) -> None:
    source = materialization_factory("30.125")

    result = interpret_materializations(operation, [source])

    assert result.operation is operation
    assert result.materialized_quantity == Decimal("30.125")
    assert result.source_materializations == (source,)


def test_multiple_materializations_produce_joint_decimal_quantity(
    operation: InvestmentOperation, materialization_factory
) -> None:
    sources = [
        materialization_factory("30.1"),
        materialization_factory("20.2"),
        materialization_factory("5.005"),
    ]

    result = interpret_materializations(operation, sources)

    assert result.materialized_quantity == Decimal("55.305")
    assert isinstance(result.materialized_quantity, Decimal)
    assert result.source_materializations == tuple(sources)


def test_foreign_materialization_is_a_domain_error(
    operation: InvestmentOperation,
) -> None:
    foreign_operation = InvestmentOperation(
        InstrumentReference("FIGI", "FOREIGN"),
        OperationDirection.BUY,
        Decimal("100"),
    )
    foreign = OperationalMaterialization(
        "foreign-1",
        foreign_operation,
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        interpret_materializations(operation, [foreign])


def test_mixed_operations_are_a_domain_error(
    operation: InvestmentOperation, materialization_factory
) -> None:
    foreign_operation = InvestmentOperation(
        InstrumentReference("FIGI", "FOREIGN"),
        OperationDirection.SELL,
        Decimal("1"),
    )
    foreign = OperationalMaterialization(
        "foreign-2",
        foreign_operation,
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        interpret_materializations(operation, [materialization_factory("1"), foreign])


def test_zero_materializations_is_a_domain_error(
    operation: InvestmentOperation,
) -> None:
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        interpret_materializations(operation, [])


@pytest.mark.parametrize(
    ("operation_value", "quantity", "sources"),
    [
        (object(), Decimal("1"), (object(),)),
        (None, Decimal("0"), ()),
    ],
)
def test_public_asset_rejects_invalid_operation(
    operation_value: object, quantity: Decimal, sources: tuple[object, ...]
) -> None:
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(
            operation_value,
            quantity,
            sources,  # type: ignore[arg-type]
        )


def test_public_asset_rejects_empty_or_mutable_provenance(
    operation: InvestmentOperation, materialization_factory
) -> None:
    source = materialization_factory("1")

    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(operation, Decimal("0"), ())
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(
            operation,
            Decimal("1"),
            [source],  # type: ignore[arg-type]
        )


def test_public_asset_rejects_foreign_or_non_materialization_sources(
    operation: InvestmentOperation,
) -> None:
    foreign_operation = InvestmentOperation(
        InstrumentReference("FIGI", "FOREIGN-DIRECT"),
        OperationDirection.BUY,
        Decimal("1"),
    )
    foreign = OperationalMaterialization(
        "foreign-direct",
        foreign_operation,
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(operation, Decimal("1"), (object(),))  # type: ignore[arg-type]
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(operation, Decimal("1"), (foreign,))


def test_public_asset_requires_exact_derived_decimal_quantity(
    operation: InvestmentOperation, materialization_factory
) -> None:
    sources = (materialization_factory("0.1"), materialization_factory("0.2"))

    valid = OperationalMaterializationInterpretation(operation, Decimal("0.3"), sources)

    assert valid.materialized_quantity == Decimal("0.3")
    assert valid.source_materializations == sources
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(operation, 0.3, sources)  # type: ignore[arg-type]
    with pytest.raises(OperationalMaterializationInterpretationDomainError):
        OperationalMaterializationInterpretation(operation, Decimal("0.4"), sources)


def test_sources_are_not_mutated_and_successive_results_remain_immutable(
    operation: InvestmentOperation, materialization_factory
) -> None:
    first = materialization_factory("30")
    second = materialization_factory("20")
    operation_values = (operation.instrument, operation.direction, operation.quantity)
    first_values = (first.operation, first.quantity, first.price, first.currency)

    earlier = interpret_materializations(operation, [first])
    later = interpret_materializations(operation, [first, second])

    assert earlier.materialized_quantity == Decimal("30")
    assert earlier.source_materializations == (first,)
    assert later.materialized_quantity == Decimal("50")
    assert operation_values == (
        operation.instrument,
        operation.direction,
        operation.quantity,
    )
    assert first_values == (
        first.operation,
        first.quantity,
        first.price,
        first.currency,
    )
    with pytest.raises((FrozenInstanceError, AttributeError)):
        earlier.materialized_quantity = Decimal("50")  # type: ignore[misc]


def test_quantity_above_operation_is_preserved_without_lifecycle(
    operation: InvestmentOperation, materialization_factory
) -> None:
    result = interpret_materializations(
        operation, [materialization_factory("60"), materialization_factory("50")]
    )

    assert result.materialized_quantity == Decimal("110")
    public_fields = [item.name for item in fields(result)]
    assert public_fields == [
        "operation",
        "materialized_quantity",
        "source_materializations",
    ]
