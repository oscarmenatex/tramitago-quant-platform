#!/usr/bin/env python3
"""Deterministic public demo of materialization interpretation."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretationDomainError,
    interpret_materializations,
)


def _materialization(
    operation: InvestmentOperation, quantity: str
) -> OperationalMaterialization:
    return OperationalMaterialization(
        operation, Decimal(quantity), Decimal("10"), CurrencyReference("USD")
    )


def main() -> None:
    operation = InvestmentOperation(
        InstrumentReference("FIGI", "INTERPRETATION-DEMO"),
        OperationDirection.BUY,
        Decimal("100"),
    )
    first = _materialization(operation, "30")
    second = _materialization(operation, "20")
    interpretation = interpret_materializations(operation, [first, second])

    print("operation quantity:", operation.quantity)
    print("source quantities:", first.quantity, second.quantity)
    print("materialized quantity:", interpretation.materialized_quantity)
    print("source facts preserved:", interpretation.source_materializations)
    assert interpretation.materialized_quantity == Decimal("50")

    foreign_operation = InvestmentOperation(
        InstrumentReference("FIGI", "FOREIGN-DEMO"),
        OperationDirection.BUY,
        Decimal("1"),
    )
    try:
        interpret_materializations(operation, [_materialization(foreign_operation, "1")])
    except OperationalMaterializationInterpretationDomainError as error:
        print("expected domain error:", type(error).__name__)
    else:
        raise AssertionError("An incompatible source must produce a domain error.")

    print("Operational Materialization Interpretation demo passed.")


if __name__ == "__main__":
    main()
