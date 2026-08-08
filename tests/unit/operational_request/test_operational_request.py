from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.execution import (
    InvestmentOperation,
    OperationalIntent,
    OperationDirection,
)
from quant_platform.operational_request import (
    OperationalRequest,
    OperationalRequestDomainError,
)


def test_formalizes_complete_intent_and_preserves_origin(
    operational_intent: OperationalIntent,
) -> None:
    request = OperationalRequest(operational_intent)

    assert request.operational_intent is operational_intent
    assert request.operations == operational_intent.operations
    assert [operation.instrument for operation in request.operations] == [
        operation.instrument for operation in operational_intent.operations
    ]
    assert [operation.direction for operation in request.operations] == [
        OperationDirection.BUY,
        OperationDirection.SELL,
    ]
    assert [operation.quantity for operation in request.operations] == [
        Decimal("3"),
        Decimal("2"),
    ]


@pytest.mark.parametrize("invalid", [None, object(), "intent"])
def test_rejects_missing_or_invalid_origin(invalid: object) -> None:
    with pytest.raises(OperationalRequestDomainError):
        OperationalRequest(invalid)  # type: ignore[arg-type]


def test_rejects_omitted_operation(operational_intent: OperationalIntent) -> None:
    with pytest.raises(OperationalRequestDomainError):
        OperationalRequest(operational_intent, operational_intent.operations[:-1])


def test_operation_order_has_no_contractual_meaning(
    operational_intent: OperationalIntent,
) -> None:
    reordered = tuple(reversed(operational_intent.operations))

    assert OperationalRequest(operational_intent, reordered).operations == reordered


def test_rejects_additional_operation(operational_intent: OperationalIntent) -> None:
    extra = InvestmentOperation(
        InstrumentReference("FIGI", "OTHER"),
        OperationDirection.BUY,
        Decimal("1"),
    )

    with pytest.raises(OperationalRequestDomainError):
        OperationalRequest(operational_intent, (*operational_intent.operations, extra))


@pytest.mark.parametrize(
    "altered",
    [
        InvestmentOperation(
            InstrumentReference("FIGI", "ALTERED"),
            OperationDirection.BUY,
            Decimal("3"),
        ),
        InvestmentOperation(
            InstrumentReference("FIGI", "BUY-ME"),
            OperationDirection.SELL,
            Decimal("3"),
        ),
        InvestmentOperation(
            InstrumentReference("FIGI", "BUY-ME"),
            OperationDirection.BUY,
            Decimal("4"),
        ),
    ],
)
def test_rejects_altered_operation(
    operational_intent: OperationalIntent,
    altered: InvestmentOperation,
) -> None:
    with pytest.raises(OperationalRequestDomainError):
        OperationalRequest(
            operational_intent,
            (altered, operational_intent.operations[1]),
        )


def test_is_observably_immutable(operational_intent: OperationalIntent) -> None:
    request = OperationalRequest(operational_intent)

    with pytest.raises((FrozenInstanceError, AttributeError)):
        request.operational_intent = operational_intent  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        request.operations = ()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        request.operations[0].quantity = Decimal("99")  # type: ignore[misc]


def test_public_fields_are_exact() -> None:
    assert [field.name for field in fields(OperationalRequest)] == [
        "operational_intent",
        "operations",
    ]
