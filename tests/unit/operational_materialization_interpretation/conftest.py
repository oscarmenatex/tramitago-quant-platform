from decimal import Decimal
from itertools import count

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
    occurrence_sequence = count(1)

    def create(
        quantity: str,
        *,
        occurrence_id: str | None = None,
    ) -> OperationalMaterialization:
        return OperationalMaterialization(
            occurrence_id or f"interpretation-{next(occurrence_sequence)}",
            operation,
            Decimal(quantity),
            Decimal("12.34"),
            CurrencyReference("USD"),
        )

    return create
