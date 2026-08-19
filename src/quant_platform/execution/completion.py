"""Immutable execution-completion classification from one interpretation."""

from dataclasses import dataclass
from enum import Enum

from quant_platform.operational_materialization_interpretation import (
    OperationalMaterializationInterpretation,
)

from .domain.exceptions import ExecutionDomainError


class ExecutionCompletionStatus(str, Enum):
    """The exhaustive completion statuses authorized by IT-034-002."""

    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True, slots=True, init=False)
class ExecutionCompletionState:
    """Immutable completion state preserving its exact source interpretation."""

    interpretation: OperationalMaterializationInterpretation
    status: ExecutionCompletionStatus

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExecutionCompletionState must be produced by "
            "classify_execution_completion."
        )

    @classmethod
    def _create(
        cls,
        interpretation: OperationalMaterializationInterpretation,
        status: ExecutionCompletionStatus,
    ) -> "ExecutionCompletionState":
        state = object.__new__(cls)
        object.__setattr__(state, "interpretation", interpretation)
        object.__setattr__(state, "status", status)
        return state


def classify_execution_completion(
    interpretation: OperationalMaterializationInterpretation,
) -> ExecutionCompletionState:
    """Classify one valid interpretation as PARTIAL or COMPLETE."""
    if not isinstance(interpretation, OperationalMaterializationInterpretation):
        raise ExecutionDomainError(
            "Execution completion requires one "
            "OperationalMaterializationInterpretation."
        )

    materialized_quantity = interpretation.materialized_quantity
    operation_quantity = interpretation.operation.quantity
    if materialized_quantity > operation_quantity:
        raise ExecutionDomainError(
            "Materialized quantity cannot exceed the operation quantity."
        )
    if materialized_quantity <= 0:
        raise ExecutionDomainError(
            "Execution completion requires a positive materialized quantity."
        )

    status = (
        ExecutionCompletionStatus.COMPLETE
        if materialized_quantity == operation_quantity
        else ExecutionCompletionStatus.PARTIAL
    )
    return ExecutionCompletionState._create(interpretation, status)


__all__ = [
    "ExecutionCompletionState",
    "ExecutionCompletionStatus",
    "classify_execution_completion",
]
