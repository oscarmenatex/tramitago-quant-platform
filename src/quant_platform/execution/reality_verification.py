"""Verification of complete internal and external execution realities."""

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from .domain import ExecutionDomainError
from .external_reality import ExternalExecutionReality
from .internal_reality import InternalExecutionReality


class ExecutionRealityVerificationOutcome(str, Enum):
    """The exhaustive outcomes of comparing two compatible realities."""

    AGREEMENT = "AGREEMENT"
    DISCREPANCY = "DISCREPANCY"


@dataclass(frozen=True, slots=True, init=False)
class ExecutionRealityVerification:
    """An immutable verification preserving both source realities."""

    internal_reality: InternalExecutionReality
    external_reality: ExternalExecutionReality
    outcome: ExecutionRealityVerificationOutcome

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "ExecutionRealityVerification must be produced by "
            "verify_execution_reality."
        )

    @classmethod
    def _create(
        cls,
        internal_reality: InternalExecutionReality,
        external_reality: ExternalExecutionReality,
        outcome: ExecutionRealityVerificationOutcome,
    ) -> "ExecutionRealityVerification":
        verification = object.__new__(cls)
        object.__setattr__(verification, "internal_reality", internal_reality)
        object.__setattr__(verification, "external_reality", external_reality)
        object.__setattr__(verification, "outcome", outcome)
        return verification


def verify_execution_reality(
    internal_reality: InternalExecutionReality,
    external_reality: ExternalExecutionReality,
) -> ExecutionRealityVerification:
    """Compare the complete execution multisets of two compatible realities."""
    if not isinstance(internal_reality, InternalExecutionReality):
        raise ExecutionDomainError(
            "Execution reality verification requires an InternalExecutionReality."
        )
    if not isinstance(external_reality, ExternalExecutionReality):
        raise ExecutionDomainError(
            "Execution reality verification requires an ExternalExecutionReality."
        )
    if internal_reality.operation != external_reality.operation:
        raise ExecutionDomainError(
            "Execution realities must represent the same InvestmentOperation."
        )
    if internal_reality.reference_time != external_reality.reference_time:
        raise ExecutionDomainError(
            "Execution realities must have equivalent reference times."
        )

    internal_executions = Counter(
        (item.quantity, item.price, item.currency)
        for item in internal_reality.materializations
    )
    external_executions = Counter(
        (item.quantity, item.price, item.currency)
        for item in external_reality.reported_executions
    )
    outcome = (
        ExecutionRealityVerificationOutcome.AGREEMENT
        if internal_executions == external_executions
        else ExecutionRealityVerificationOutcome.DISCREPANCY
    )
    return ExecutionRealityVerification._create(
        internal_reality,
        external_reality,
        outcome,
    )


__all__ = [
    "ExecutionRealityVerification",
    "ExecutionRealityVerificationOutcome",
    "verify_execution_reality",
]
