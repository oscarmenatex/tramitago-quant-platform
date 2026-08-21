"""Explicit required universe for a future Reconciliation evaluation."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.operational_submission import OperationalSubmission

from .domain import ExecutionDomainError, InvestmentOperation


_Requirement = TypeVar("_Requirement")


@dataclass(frozen=True, slots=True)
class ReconciliationReferenceTime:
    """The single instant governed by a required Reconciliation scope."""

    value: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.value, datetime):
            raise ExecutionDomainError(
                "ReconciliationReferenceTime value must be a datetime."
            )
        try:
            offset = self.value.utcoffset()
        except Exception as error:
            raise ExecutionDomainError(
                "ReconciliationReferenceTime requires a determinable UTC offset."
            ) from error
        if self.value.tzinfo is None or offset is None:
            raise ExecutionDomainError(
                "ReconciliationReferenceTime requires a timezone-aware datetime."
            )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RequiredReconciliationScope:
    """An immutable snapshot of the explicitly required Reconciliation universe."""

    reference_time: ReconciliationReferenceTime
    required_positions: tuple[InstrumentReference, ...]
    required_monetary_balances: tuple[CurrencyReference, ...]
    required_orders: tuple[OperationalSubmission, ...]
    required_executions: tuple[InvestmentOperation, ...]

    def __init__(self) -> None:
        raise ExecutionDomainError(
            "RequiredReconciliationScope must be produced by "
            "declare_required_reconciliation_scope."
        )

    @classmethod
    def _create(
        cls,
        reference_time: ReconciliationReferenceTime,
        required_positions: tuple[InstrumentReference, ...],
        required_monetary_balances: tuple[CurrencyReference, ...],
        required_orders: tuple[OperationalSubmission, ...],
        required_executions: tuple[InvestmentOperation, ...],
    ) -> "RequiredReconciliationScope":
        scope = object.__new__(cls)
        object.__setattr__(scope, "reference_time", reference_time)
        object.__setattr__(scope, "required_positions", required_positions)
        object.__setattr__(
            scope, "required_monetary_balances", required_monetary_balances
        )
        object.__setattr__(scope, "required_orders", required_orders)
        object.__setattr__(scope, "required_executions", required_executions)
        return scope

    @property
    def _semantic_identity(self) -> tuple[object, ...]:
        return (
            self.reference_time,
            frozenset(self.required_positions),
            frozenset(self.required_monetary_balances),
            frozenset(id(order) for order in self.required_orders),
            frozenset(self.required_executions),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RequiredReconciliationScope):
            return NotImplemented
        return self._semantic_identity == other._semantic_identity

    def __hash__(self) -> int:
        return hash(self._semantic_identity)


def _snapshot_unique(
    values: Iterable[_Requirement],
    expected_type: type[_Requirement],
    label: str,
    ordering_key: Callable[[_Requirement], object],
) -> tuple[_Requirement, ...]:
    try:
        snapshot = tuple(values)
    except (TypeError, RuntimeError) as error:
        raise ExecutionDomainError(f"{label} must be an iterable.") from error
    if not all(isinstance(value, expected_type) for value in snapshot):
        raise ExecutionDomainError(
            f"{label} must contain only {expected_type.__name__} values."
        )
    return tuple(sorted(dict.fromkeys(snapshot), key=ordering_key))


def _snapshot_unique_orders(
    values: Iterable[OperationalSubmission],
) -> tuple[OperationalSubmission, ...]:
    try:
        snapshot = tuple(values)
    except (TypeError, RuntimeError) as error:
        raise ExecutionDomainError("required_orders must be an iterable.") from error
    if not all(isinstance(value, OperationalSubmission) for value in snapshot):
        raise ExecutionDomainError(
            "required_orders must contain only OperationalSubmission values."
        )
    unique_by_identity = {id(value): value for value in snapshot}
    return tuple(
        unique_by_identity[identity] for identity in sorted(unique_by_identity)
    )


def declare_required_reconciliation_scope(
    reference_time: ReconciliationReferenceTime,
    required_positions: Iterable[InstrumentReference] = (),
    required_monetary_balances: Iterable[CurrencyReference] = (),
    required_orders: Iterable[OperationalSubmission] = (),
    required_executions: Iterable[InvestmentOperation] = (),
) -> RequiredReconciliationScope:
    """Snapshot and publish an explicit required Reconciliation universe."""
    if not isinstance(reference_time, ReconciliationReferenceTime):
        raise ExecutionDomainError(
            "RequiredReconciliationScope requires a ReconciliationReferenceTime."
        )

    positions = _snapshot_unique(
        required_positions,
        InstrumentReference,
        "required_positions",
        lambda value: value.semantic_identity,
    )
    balances = _snapshot_unique(
        required_monetary_balances,
        CurrencyReference,
        "required_monetary_balances",
        lambda value: value.semantic_identity,
    )
    executions = _snapshot_unique(
        required_executions,
        InvestmentOperation,
        "required_executions",
        lambda value: (
            value.instrument.semantic_identity,
            value.direction.value,
            value.quantity,
        ),
    )
    return RequiredReconciliationScope._create(
        reference_time,
        positions,
        balances,
        _snapshot_unique_orders(required_orders),
        executions,
    )


__all__ = [
    "ReconciliationReferenceTime",
    "RequiredReconciliationScope",
    "declare_required_reconciliation_scope",
]
