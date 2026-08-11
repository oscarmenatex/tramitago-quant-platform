from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization


@pytest.fixture
def operation() -> InvestmentOperation:
    return InvestmentOperation(
        InstrumentReference("FIGI", "INTERPRETATION-TEST"),
        OperationDirection.BUY,
        Decimal("100"),
    )


@pytest.fixture
def materialization_factory(operation: InvestmentOperation):
    def create(quantity: str) -> OperationalMaterialization:
        return OperationalMaterialization(
            operation,
            Decimal(quantity),
            Decimal("12.34"),
            CurrencyReference("USD"),
        )

    return create
