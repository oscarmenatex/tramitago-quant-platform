"""Qualification of completion for an explicit Reconciliation scope."""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from quant_platform.economic_reality_verification import (
    EconomicRealityDimension,
    EconomicRealityVerification,
    EconomicRealityVerificationOutcome,
)

from .domain import ExecutionDomainError
from .order_reality_verification import (
    OrderRealityVerification,
    OrderRealityVerificationOutcome,
)
from .reality_verification import (
    ExecutionRealityVerification,
    ExecutionRealityVerificationOutcome,
)
from .reconciliation_scope import RequiredReconciliationScope


class ReconciliationCompletionCondition(str, Enum):
    """The exhaustive completion conditions for one required scope."""

    RECONCILED = "RECONCILED"
    DIVERGENT = "DIVERGENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True, slots=True, init=False)
class ReconciliationCompletionQualification:
    """Immutable qualification preserving only the evidence actually used."""

    required_scope: RequiredReconciliationScope
    economic_verification: EconomicRealityVerification | None
    order_verifications: tuple[OrderRealityVerification, ...]
    execution_verifications: tuple[ExecutionRealityVerification, ...]
    condition: ReconciliationCompletionCondition

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise ExecutionDomainError(
            "ReconciliationCompletionQualification must be produced by "
            "qualify_reconciliation_completion."
        )

    @classmethod
    def _create(
        cls,
        required_scope: RequiredReconciliationScope,
        economic_verification: EconomicRealityVerification | None,
        order_verifications: tuple[OrderRealityVerification, ...],
        execution_verifications: tuple[ExecutionRealityVerification, ...],
        condition: ReconciliationCompletionCondition,
    ) -> "ReconciliationCompletionQualification":
        qualification = object.__new__(cls)
        object.__setattr__(qualification, "required_scope", required_scope)
        object.__setattr__(
            qualification, "economic_verification", economic_verification
        )
        object.__setattr__(qualification, "order_verifications", order_verifications)
        object.__setattr__(
            qualification, "execution_verifications", execution_verifications
        )
        object.__setattr__(qualification, "condition", condition)
        return qualification


def _snapshot_verifications(
    values: Iterable[object], expected_type: type, label: str
) -> tuple[object, ...]:
    try:
        snapshot = tuple(values)
    except (TypeError, RuntimeError) as error:
        raise ExecutionDomainError(f"{label} must be an iterable.") from error
    if not all(isinstance(value, expected_type) for value in snapshot):
        raise ExecutionDomainError(
            f"{label} must contain only {expected_type.__name__} values."
        )
    return snapshot


def _unique_instances(values: tuple[object, ...]) -> tuple[object, ...]:
    unique: dict[int, object] = {}
    for value in values:
        unique.setdefault(id(value), value)
    return tuple(unique.values())


def _same_instant(scope: RequiredReconciliationScope, reference_time: object) -> bool:
    return scope.reference_time.value == reference_time.value


def qualify_reconciliation_completion(
    required_scope: RequiredReconciliationScope,
    economic_verification: EconomicRealityVerification | None = None,
    order_verifications: Iterable[OrderRealityVerification] = (),
    execution_verifications: Iterable[ExecutionRealityVerification] = (),
) -> ReconciliationCompletionQualification:
    """Qualify whether all requirements in an explicit scope are satisfied."""
    if not isinstance(required_scope, RequiredReconciliationScope):
        raise ExecutionDomainError(
            "Reconciliation completion requires a RequiredReconciliationScope."
        )
    if economic_verification is not None and not isinstance(
        economic_verification, EconomicRealityVerification
    ):
        raise ExecutionDomainError(
            "economic_verification must be an EconomicRealityVerification or None."
        )

    order_snapshot = _snapshot_verifications(
        order_verifications, OrderRealityVerification, "order_verifications"
    )
    execution_snapshot = _snapshot_verifications(
        execution_verifications,
        ExecutionRealityVerification,
        "execution_verifications",
    )

    divergent = False
    insufficient = False
    uses_economic = bool(
        required_scope.required_positions or required_scope.required_monetary_balances
    )

    if uses_economic:
        if economic_verification is None:
            insufficient = True
        else:
            economic_time = economic_verification.internal_reality.reference_time
            if not _same_instant(required_scope, economic_time):
                raise ExecutionDomainError(
                    "Required economic verification has an incompatible reference time."
                )
            required_economic = (
                (
                    required_scope.required_positions,
                    economic_verification.position_results,
                    EconomicRealityDimension.POSITION,
                ),
                (
                    required_scope.required_monetary_balances,
                    economic_verification.monetary_results,
                    EconomicRealityDimension.MONETARY_BALANCE,
                ),
            )
            for requirements, results, dimension in required_economic:
                outcomes = {
                    result.identity: result.outcome
                    for result in results
                    if result.dimension is dimension
                }
                for requirement in requirements:
                    outcome = outcomes.get(requirement)
                    if outcome is EconomicRealityVerificationOutcome.DISCREPANCY:
                        divergent = True
                    elif outcome is not EconomicRealityVerificationOutcome.AGREEMENT:
                        insufficient = True

    required_order_ids = {id(order) for order in required_scope.required_orders}
    order_by_requirement: dict[int, OrderRealityVerification] = {}
    for item in _unique_instances(order_snapshot):
        verification = item
        submission = verification.internal_reality.submission
        requirement_id = id(submission)
        if requirement_id not in required_order_ids:
            continue
        if not _same_instant(
            required_scope, verification.internal_reality.reference_time
        ):
            raise ExecutionDomainError(
                "Required order verification has an incompatible reference time."
            )
        if requirement_id in order_by_requirement:
            raise ExecutionDomainError(
                "Distinct order verifications target the same required order."
            )
        order_by_requirement[requirement_id] = verification

    for requirement in required_scope.required_orders:
        verification = order_by_requirement.get(id(requirement))
        if verification is None:
            insufficient = True
        elif verification.outcome is OrderRealityVerificationOutcome.DISCREPANCY:
            divergent = True

    required_executions = set(required_scope.required_executions)
    execution_by_requirement: dict[object, ExecutionRealityVerification] = {}
    for item in _unique_instances(execution_snapshot):
        verification = item
        operation = verification.internal_reality.operation
        if operation not in required_executions:
            continue
        if not _same_instant(
            required_scope, verification.internal_reality.reference_time
        ):
            raise ExecutionDomainError(
                "Required execution verification has an incompatible reference time."
            )
        if operation in execution_by_requirement:
            raise ExecutionDomainError(
                "Distinct execution verifications target the same required execution."
            )
        execution_by_requirement[operation] = verification

    for requirement in required_scope.required_executions:
        verification = execution_by_requirement.get(requirement)
        if verification is None:
            insufficient = True
        elif verification.outcome is ExecutionRealityVerificationOutcome.DISCREPANCY:
            divergent = True

    if divergent:
        condition = ReconciliationCompletionCondition.DIVERGENT
    elif insufficient:
        condition = ReconciliationCompletionCondition.INSUFFICIENT_EVIDENCE
    else:
        condition = ReconciliationCompletionCondition.RECONCILED

    return ReconciliationCompletionQualification._create(
        required_scope,
        economic_verification if uses_economic else None,
        tuple(order_by_requirement.values()),
        tuple(execution_by_requirement.values()),
        condition,
    )


__all__ = [
    "ReconciliationCompletionCondition",
    "ReconciliationCompletionQualification",
    "qualify_reconciliation_completion",
]
