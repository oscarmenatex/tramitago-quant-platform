from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
from inspect import signature

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import (
    ExecutionCompletionState,
    ExecutionCompletionStatus,
    ExecutionDomainError,
    InvestmentOperation,
    OperationDirection,
    classify_execution_completion,
)
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretation,
    interpret_materializations,
)


def _interpretation(
    quantity: str,
    *materialized_quantities: str,
) -> OperationalMaterializationInterpretation:
    operation = InvestmentOperation(
        InstrumentReference("FIGI", f"COMPLETION-{quantity}"),
        OperationDirection.BUY,
        Decimal(quantity),
    )
    sources = tuple(
        OperationalMaterialization(
            f"completion-{index}",
            operation,
            Decimal(materialized),
            Decimal("12.34"),
            CurrencyReference("USD"),
        )
        for index, materialized in enumerate(materialized_quantities, start=1)
    )
    return interpret_materializations(operation, sources)


def test_positive_quantity_below_operation_is_partial() -> None:
    interpretation = _interpretation("100", "30")

    state = classify_execution_completion(interpretation)

    assert state.status is ExecutionCompletionStatus.PARTIAL


def test_quantity_equal_to_operation_is_complete() -> None:
    interpretation = _interpretation("100", "30", "70")

    state = classify_execution_completion(interpretation)

    assert state.status is ExecutionCompletionStatus.COMPLETE


def test_classification_uses_exact_decimal_comparison() -> None:
    partial = classify_execution_completion(_interpretation("0.3", "0.1"))
    complete = classify_execution_completion(_interpretation("0.3", "0.1", "0.2"))

    assert partial.status is ExecutionCompletionStatus.PARTIAL
    assert complete.status is ExecutionCompletionStatus.COMPLETE
    assert isinstance(complete.interpretation.materialized_quantity, Decimal)


def test_state_preserves_interpretation_and_transitive_operation_provenance() -> None:
    interpretation = _interpretation("100", "30")

    state = classify_execution_completion(interpretation)

    assert state.interpretation is interpretation
    assert state.interpretation.operation is interpretation.operation
    assert state.interpretation.source_materializations == (
        interpretation.source_materializations
    )


def test_classification_does_not_mutate_any_source() -> None:
    interpretation = _interpretation("100", "30")
    operation = interpretation.operation
    materialization = interpretation.source_materializations[0]
    before = (
        operation.instrument,
        operation.direction,
        operation.quantity,
        interpretation.materialized_quantity,
        interpretation.source_materializations,
        materialization.occurrence_id,
        materialization.quantity,
        materialization.price,
        materialization.currency,
    )

    classify_execution_completion(interpretation)

    assert before == (
        operation.instrument,
        operation.direction,
        operation.quantity,
        interpretation.materialized_quantity,
        interpretation.source_materializations,
        materialization.occurrence_id,
        materialization.quantity,
        materialization.price,
        materialization.currency,
    )


def test_successive_classifications_do_not_change_earlier_state() -> None:
    partial_interpretation = _interpretation("100", "30")
    complete_interpretation = _interpretation("100", "30", "70")

    earlier = classify_execution_completion(partial_interpretation)
    later = classify_execution_completion(complete_interpretation)

    assert earlier.status is ExecutionCompletionStatus.PARTIAL
    assert earlier.interpretation is partial_interpretation
    assert later.status is ExecutionCompletionStatus.COMPLETE
    assert later.interpretation is complete_interpretation
    with pytest.raises((FrozenInstanceError, AttributeError)):
        earlier.status = ExecutionCompletionStatus.COMPLETE  # type: ignore[misc]


def test_over_materialization_raises_existing_execution_error() -> None:
    interpretation = _interpretation("100", "60", "50")

    with pytest.raises(ExecutionDomainError):
        classify_execution_completion(interpretation)

    assert interpretation.materialized_quantity == Decimal("110")


def test_public_action_accepts_only_one_interpretation_argument() -> None:
    parameters = tuple(signature(classify_execution_completion).parameters)

    assert parameters == ("interpretation",)
    with pytest.raises(ExecutionDomainError):
        classify_execution_completion(object())  # type: ignore[arg-type]


def test_state_has_only_normative_fields_and_controlled_construction() -> None:
    assert [field.name for field in fields(ExecutionCompletionState)] == [
        "interpretation",
        "status",
    ]
    with pytest.raises(ExecutionDomainError):
        ExecutionCompletionState()
