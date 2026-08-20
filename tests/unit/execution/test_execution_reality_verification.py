from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import (
    ExecutionDomainError,
    ExecutionRealityReferenceTime,
    ExecutionRealityVerification,
    ExecutionRealityVerificationOutcome,
    ExternalExecutionAuthority,
    InvestmentOperation,
    InternalExecutionAuthority,
    OperationDirection,
    ReportedExecution,
    SupportingExecutionEvidence,
    SupportingInternalExecutionEvidence,
    qualify_external_execution_reality,
    qualify_internal_execution_reality,
    verify_execution_reality,
)
from quant_platform.operational_materialization import OperationalMaterialization


UTC_TIME = datetime(2026, 8, 20, 12, tzinfo=timezone.utc)


def operation(identity: str = "PRIMARY") -> InvestmentOperation:
    return InvestmentOperation(
        InstrumentReference("FIGI", identity),
        OperationDirection.BUY,
        Decimal("10"),
    )


def internal_reality(
    investment_operation: InvestmentOperation,
    executions: tuple[tuple[str, str, str, str], ...] = (),
    *,
    reference_time: ExecutionRealityReferenceTime | None = None,
):
    materializations = tuple(
        OperationalMaterialization(
            execution_id,
            investment_operation,
            Decimal(quantity),
            Decimal(price),
            CurrencyReference(currency),
        )
        for execution_id, quantity, price, currency in executions
    )
    evidence = SupportingInternalExecutionEvidence(
        InternalExecutionAuthority("ledger"),
        reference_time or ExecutionRealityReferenceTime(UTC_TIME),
        UTC_TIME,
        investment_operation,
        materializations,
    )
    return qualify_internal_execution_reality((evidence,))


def external_reality(
    investment_operation: InvestmentOperation,
    executions: tuple[tuple[str, str, str, str], ...] = (),
    *,
    reference_time: ExecutionRealityReferenceTime | None = None,
):
    reported = tuple(
        ReportedExecution(
            execution_id,
            Decimal(quantity),
            Decimal(price),
            CurrencyReference(currency),
        )
        for execution_id, quantity, price, currency in executions
    )
    evidence = SupportingExecutionEvidence(
        ExternalExecutionAuthority("broker"),
        reference_time or ExecutionRealityReferenceTime(UTC_TIME),
        UTC_TIME,
        investment_operation,
        reported,
    )
    return qualify_external_execution_reality((evidence,))


@pytest.mark.parametrize(
    ("internal", "external"),
    [
        ((), ()),
        ((("internal-id", "2", "100", "USD"),), (("external-id", "2", "100", "USD"),)),
        (
            (("i-1", "2", "100", "USD"), ("i-2", "2", "100", "USD")),
            (("e-1", "2", "100", "USD"), ("e-2", "2", "100", "USD")),
        ),
        (
            (("i-1", "2", "100", "USD"), ("i-2", "3", "101", "EUR")),
            (("e-2", "3", "101", "EUR"), ("e-1", "2", "100", "USD")),
        ),
    ],
)
def test_agreement_uses_complete_unordered_multisets_and_ignores_cross_boundary_ids(
    internal: tuple[tuple[str, str, str, str], ...],
    external: tuple[tuple[str, str, str, str], ...],
) -> None:
    scope = operation()

    verification = verify_execution_reality(
        internal_reality(scope, internal), external_reality(scope, external)
    )

    assert verification.outcome is ExecutionRealityVerificationOutcome.AGREEMENT


@pytest.mark.parametrize(
    ("internal", "external"),
    [
        ((("i-1", "2", "100", "USD"),), ()),
        ((("i-1", "2", "100", "USD"),), (("e-1", "3", "100", "USD"),)),
        ((("i-1", "2", "100", "USD"),), (("e-1", "2", "101", "USD"),)),
        ((("i-1", "2", "100", "USD"),), (("e-1", "2", "100", "EUR"),)),
        (
            (("i-1", "2", "100", "USD"), ("i-2", "2", "100", "USD")),
            (("e-1", "2", "100", "USD"),),
        ),
    ],
)
def test_discrepancy_covers_cardinality_and_each_execution_meaning_dimension(
    internal: tuple[tuple[str, str, str, str], ...],
    external: tuple[tuple[str, str, str, str], ...],
) -> None:
    scope = operation()

    verification = verify_execution_reality(
        internal_reality(scope, internal), external_reality(scope, external)
    )

    assert verification.outcome is ExecutionRealityVerificationOutcome.DISCREPANCY


def test_rejects_incompatible_operations() -> None:
    with pytest.raises(ExecutionDomainError):
        verify_execution_reality(
            internal_reality(operation("ONE")),
            external_reality(operation("TWO")),
        )


def test_reference_times_compare_by_instant_across_offsets() -> None:
    scope = operation()
    internal = internal_reality(
        scope, reference_time=ExecutionRealityReferenceTime(UTC_TIME)
    )
    external = external_reality(
        scope,
        reference_time=ExecutionRealityReferenceTime(
            UTC_TIME.astimezone(timezone(timedelta(hours=-4)))
        ),
    )

    assert (
        verify_execution_reality(internal, external).outcome
        is ExecutionRealityVerificationOutcome.AGREEMENT
    )


def test_rejects_incompatible_reference_times() -> None:
    scope = operation()
    with pytest.raises(ExecutionDomainError):
        verify_execution_reality(
            internal_reality(scope),
            external_reality(
                scope,
                reference_time=ExecutionRealityReferenceTime(
                    UTC_TIME + timedelta(seconds=1)
                ),
            ),
        )


def test_rejects_invalid_internal_input_type() -> None:
    with pytest.raises(ExecutionDomainError):
        verify_execution_reality(object(), object())  # type: ignore[arg-type]


def test_rejects_invalid_external_input_type() -> None:
    with pytest.raises(ExecutionDomainError):
        verify_execution_reality(  # type: ignore[arg-type]
            internal_reality(operation()), object()
        )


def test_preserves_source_identity_and_is_immutable() -> None:
    scope = operation()
    internal = internal_reality(scope)
    external = external_reality(scope)
    verification = verify_execution_reality(internal, external)

    assert verification.internal_reality is internal
    assert verification.external_reality is external
    with pytest.raises(FrozenInstanceError):
        verification.outcome = (  # type: ignore[misc]
            ExecutionRealityVerificationOutcome.DISCREPANCY
        )


def test_contract_surface_is_exact_and_direct_construction_is_forbidden() -> None:
    assert list(ExecutionRealityVerificationOutcome) == [
        ExecutionRealityVerificationOutcome.AGREEMENT,
        ExecutionRealityVerificationOutcome.DISCREPANCY,
    ]
    assert not hasattr(ExecutionRealityVerificationOutcome, "NOT_COMPARABLE")
    assert [field.name for field in fields(ExecutionRealityVerification)] == [
        "internal_reality",
        "external_reality",
        "outcome",
    ]
    assert tuple(verify_execution_reality.__annotations__) == (
        "internal_reality",
        "external_reality",
        "return",
    )
    with pytest.raises(ExecutionDomainError):
        ExecutionRealityVerification()
    with pytest.raises(TypeError):
        ExecutionRealityVerification(  # type: ignore[call-arg]
            internal_reality(operation()),
            external_reality(operation()),
            ExecutionRealityVerificationOutcome.DISCREPANCY,
        )
