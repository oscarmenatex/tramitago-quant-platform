from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.execution import (
    CapitalProtectionAuthority,
    CapitalProtectionReferenceTime,
    ExecutionDomainError,
    ExternalFailureCapitalProtectionCondition,
    ExternalFailureCapitalProtectionQualification,
    ExternalFailureAuthority,
    ExternalFailureClass,
    ExternalFailureObligation,
    ExternalFailureReferenceTime,
    SupportingCapitalProtectionEvidence,
    SupportingExternalFailureEvidence,
    prepare_operational_request,
    qualify_external_failure_capital_protection,
    recognize_external_failure,
)
from quant_platform.portfolio import PortfolioState


REFERENCE_TIME = datetime(2026, 8, 21, 12, tzinfo=timezone.utc)


def _failure(target: PortfolioState):
    context = prepare_operational_request(target)
    evidence = SupportingExternalFailureEvidence(
        authority=ExternalFailureAuthority("failure authority"),
        obligation=ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        failure_class=ExternalFailureClass.INTERACTION_FAILURE,
        reference_time=ExternalFailureReferenceTime(REFERENCE_TIME),
        observed_at_utc=REFERENCE_TIME,
        context=context,
    )
    return recognize_external_failure((evidence,))


def _evidence(
    failure,
    *,
    reference_time: datetime = REFERENCE_TIME,
    authority: str = "capital authority",
    basis_reference: str = "basis-v1",
    observed_at_utc: datetime = REFERENCE_TIME,
):
    return SupportingCapitalProtectionEvidence(
        authority=CapitalProtectionAuthority(authority),
        reference_time=CapitalProtectionReferenceTime(reference_time),
        observed_at_utc=observed_at_utc,
        external_failure=failure,
        basis_reference=basis_reference,
    )


def test_one_applicable_evidence_produces_protected(target: PortfolioState) -> None:
    failure = _failure(target)
    evidence = _evidence(failure)
    result = qualify_external_failure_capital_protection(
        failure, CapitalProtectionReferenceTime(REFERENCE_TIME), (evidence,)
    )
    assert result.condition is ExternalFailureCapitalProtectionCondition.PROTECTED
    assert result.supporting_evidence == (evidence,)
    assert result.supporting_evidence[0] is evidence
    assert result.external_failure is failure


def test_zero_or_only_extraneous_evidence_is_not_demonstrated(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    other_failure = _failure(target)
    reference_time = CapitalProtectionReferenceTime(REFERENCE_TIME)
    cases = (
        (),
        (_evidence(other_failure),),
        (_evidence(failure, reference_time=REFERENCE_TIME + timedelta(seconds=1)),),
    )
    for evidence in cases:
        result = qualify_external_failure_capital_protection(
            failure, reference_time, evidence
        )
        assert (
            result.condition
            is ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED
        )
        assert result.supporting_evidence == ()


def test_mixed_extraneous_evidence_is_ignored(target: PortfolioState) -> None:
    failure = _failure(target)
    applicable = _evidence(failure)
    extraneous = _evidence(_failure(target))
    result = qualify_external_failure_capital_protection(
        failure,
        CapitalProtectionReferenceTime(REFERENCE_TIME),
        (extraneous, applicable),
    )
    assert result.condition is ExternalFailureCapitalProtectionCondition.PROTECTED
    assert result.supporting_evidence == (applicable,)


def test_failure_matching_uses_instance_identity(target: PortfolioState) -> None:
    first = _failure(target)
    structurally_equal = recognize_external_failure(first.supporting_evidence)
    assert structurally_equal == first
    assert structurally_equal is not first
    result = qualify_external_failure_capital_protection(
        first,
        CapitalProtectionReferenceTime(REFERENCE_TIME),
        (_evidence(structurally_equal),),
    )
    assert (
        result.condition is ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED
    )


def test_reference_time_equivalence_is_by_instant(target: PortfolioState) -> None:
    failure = _failure(target)
    same_instant = REFERENCE_TIME.astimezone(timezone(timedelta(hours=-4)))
    applicable = _evidence(failure, reference_time=same_instant)
    result = qualify_external_failure_capital_protection(
        failure, CapitalProtectionReferenceTime(REFERENCE_TIME), (applicable,)
    )
    assert result.condition is ExternalFailureCapitalProtectionCondition.PROTECTED


def test_evidence_invariants(target: PortfolioState) -> None:
    failure = _failure(target)
    with pytest.raises(ExecutionDomainError):
        CapitalProtectionAuthority("")
    with pytest.raises(ExecutionDomainError):
        CapitalProtectionReferenceTime(datetime(2026, 8, 21))
    with pytest.raises(ExecutionDomainError):
        _evidence(failure, observed_at_utc=datetime(2026, 8, 21))
    with pytest.raises(ExecutionDomainError):
        _evidence(
            failure,
            observed_at_utc=datetime(2026, 8, 21, tzinfo=timezone(timedelta(hours=1))),
        )
    with pytest.raises(ExecutionDomainError):
        _evidence(failure, basis_reference=" ")
    with pytest.raises(ExecutionDomainError):
        SupportingCapitalProtectionEvidence(
            authority="authority",  # type: ignore[arg-type]
            reference_time=CapitalProtectionReferenceTime(REFERENCE_TIME),
            observed_at_utc=REFERENCE_TIME,
            external_failure=failure,
            basis_reference="basis-v1",
        )


def test_invalid_evidence_members_are_rejected(target: PortfolioState) -> None:
    failure = _failure(target)
    with pytest.raises(ExecutionDomainError):
        qualify_external_failure_capital_protection(
            failure,
            CapitalProtectionReferenceTime(REFERENCE_TIME),
            (_evidence(failure), object()),  # type: ignore[arg-type]
        )


def test_duplicates_are_by_instance_and_all_distinct_provenance_is_preserved(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    first = _evidence(failure)
    equal_but_distinct = _evidence(failure)
    other_authority = _evidence(failure, authority="another authority")
    other_basis = _evidence(failure, basis_reference="basis-v2")
    assert equal_but_distinct == first and equal_but_distinct is not first
    result = qualify_external_failure_capital_protection(
        failure,
        CapitalProtectionReferenceTime(REFERENCE_TIME),
        (first, first, equal_but_distinct, other_authority, other_basis),
    )
    assert result.supporting_evidence == (
        first,
        equal_but_distinct,
        other_authority,
        other_basis,
    )
    assert result.supporting_evidence[0] is first
    assert result.supporting_evidence[1] is equal_but_distinct


def test_result_and_public_contracts_are_immutable_and_exact(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    evidence = _evidence(failure)
    supplied = [evidence]
    result = qualify_external_failure_capital_protection(
        failure, CapitalProtectionReferenceTime(REFERENCE_TIME), supplied
    )
    supplied.clear()
    assert result.supporting_evidence == (evidence,)
    assert [field.name for field in fields(result)] == [
        "external_failure",
        "reference_time",
        "condition",
        "supporting_evidence",
    ]
    with pytest.raises(FrozenInstanceError):
        result.condition = ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        evidence.basis_reference = "changed"  # type: ignore[misc]


def test_direct_construction_is_rejected() -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalFailureCapitalProtectionQualification()
    with pytest.raises(ExecutionDomainError):
        ExternalFailureCapitalProtectionQualification(object())  # type: ignore[call-arg]


def test_condition_is_exactly_binary() -> None:
    assert list(ExternalFailureCapitalProtectionCondition) == [
        ExternalFailureCapitalProtectionCondition.PROTECTED,
        ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED,
    ]
