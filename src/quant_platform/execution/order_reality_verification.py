"""Verification of complete internal and external order realities."""

from dataclasses import dataclass
from enum import Enum

from .domain import ExecutionDomainError
from .internal_order_reality import InternalOrderReality
from .order_reality import ExternalOrderReality


class OrderRealityVerificationOutcome(str, Enum):
    """The exhaustive outcomes of comparing two compatible order realities."""

    AGREEMENT = "AGREEMENT"
    DISCREPANCY = "DISCREPANCY"


@dataclass(frozen=True, slots=True, init=False)
class OrderRealityVerification:
    """An immutable verification preserving both source order realities."""

    internal_reality: InternalOrderReality
    external_reality: ExternalOrderReality
    outcome: OrderRealityVerificationOutcome

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "OrderRealityVerification must be produced by verify_order_reality."
        )

    @classmethod
    def _create(
        cls,
        internal_reality: InternalOrderReality,
        external_reality: ExternalOrderReality,
        outcome: OrderRealityVerificationOutcome,
    ) -> "OrderRealityVerification":
        verification = object.__new__(cls)
        object.__setattr__(verification, "internal_reality", internal_reality)
        object.__setattr__(verification, "external_reality", external_reality)
        object.__setattr__(verification, "outcome", outcome)
        return verification


def verify_order_reality(
    internal_reality: InternalOrderReality,
    external_reality: ExternalOrderReality,
) -> OrderRealityVerification:
    """Compare the complete meanings sets of two compatible order realities."""
    if not isinstance(internal_reality, InternalOrderReality):
        raise ExecutionDomainError(
            "Order reality verification requires an InternalOrderReality."
        )
    if not isinstance(external_reality, ExternalOrderReality):
        raise ExecutionDomainError(
            "Order reality verification requires an ExternalOrderReality."
        )
    if internal_reality.submission is not external_reality.submission:
        raise ExecutionDomainError(
            "Order realities must preserve the same OperationalSubmission instance."
        )
    if internal_reality.reference_time != external_reality.reference_time:
        raise ExecutionDomainError(
            "Order realities must have equivalent reference times."
        )

    outcome = (
        OrderRealityVerificationOutcome.AGREEMENT
        if internal_reality.meanings == external_reality.meanings
        else OrderRealityVerificationOutcome.DISCREPANCY
    )
    return OrderRealityVerification._create(
        internal_reality,
        external_reality,
        outcome,
    )


__all__ = [
    "OrderRealityVerification",
    "OrderRealityVerificationOutcome",
    "verify_order_reality",
]
