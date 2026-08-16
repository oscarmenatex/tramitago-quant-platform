from decimal import Decimal
from itertools import count

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization


@pytest.fixture
def instrument() -> InstrumentReference:
    return InstrumentReference("FIGI", "CONSEQUENCE-TEST")


@pytest.fixture
def usd() -> CurrencyReference:
    return CurrencyReference("USD")


@pytest.fixture
def materialization_factory(instrument, usd):
    occurrence_sequence = count(1)

    def create(
        direction: OperationDirection,
        materialized_quantity: str,
        price: str,
        *,
        operation_quantity: str = "100",
        currency: CurrencyReference = usd,
        source_instrument: InstrumentReference = instrument,
    ) -> OperationalMaterialization:
        operation = InvestmentOperation(
            source_instrument, direction, Decimal(operation_quantity)
        )
        return OperationalMaterialization(
            f"economic-consequence-{next(occurrence_sequence)}",
            operation,
            Decimal(materialized_quantity),
            Decimal(price),
            currency,
        )

    return create
