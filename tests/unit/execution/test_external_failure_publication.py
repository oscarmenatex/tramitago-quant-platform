from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timezone

import pytest

from quant_platform.execution import (
    CapitalProtectionAuthority,
    CapitalProtectionReferenceTime,
    ExecutionDomainError,
    ExternalFailureAuthority,
    ExternalFailureCapitalProtectionCondition,
    ExternalFailureClass,
    ExternalFailureObligation,
    ExternalFailurePublication,
    ExternalFailureReferenceTime,
    SupportingCapitalProtectionEvidence,
    SupportingExternalFailureEvidence,
    prepare_operational_request,
    publish_external_failure,
    qualify_external_failure_capital_protection,
    recognize_external_failure,
)
from quant_platform.portfolio import PortfolioState


REFERENCE_TIME = datetime(2026, 8, 21, 12, tzinfo=timezone.utc)


def _failure(target: PortfolioState):
    evidence = SupportingExternalFailureEvidence(
        authority=ExternalFailureAuthority("failure authority"),
        obligation=ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        failure_class=ExternalFailureClass.INTERACTION_FAILURE,
        reference_time=ExternalFailureReferenceTime(REFERENCE_TIME),
        observed_at_utc=REFERENCE_TIME,
        context=prepare_operational_request(target),
    )
    return recognize_external_failure((evidence,))


def _qualification(failure, *, protected: bool):
    evidence = ()
    if protected:
        evidence = (
            SupportingCapitalProtectionEvidence(
                authority=CapitalProtectionAuthority("capital authority"),
                reference_time=CapitalProtectionReferenceTime(REFERENCE_TIME),
                observed_at_utc=REFERENCE_TIME,
                external_failure=failure,
                basis_reference="basis-v1",
            ),
        )
    return qualify_external_failure_capital_protection(
        failure, CapitalProtectionReferenceTime(REFERENCE_TIME), evidence
    )


@pytest.mark.parametrize("protected", [True, False])
def test_both_qualification_outcomes_are_published_by_exact_identity(
    target: PortfolioState, protected: bool
) -> None:
    failure = _failure(target)
    qualification = _qualification(failure, protected=protected)
    result = publish_external_failure(failure, qualification)

    assert isinstance(result, ExternalFailurePublication)
    assert result.external_failure is failure
    assert result.capital_protection_qualification is qualification
    expected = (
        ExternalFailureCapitalProtectionCondition.PROTECTED
        if protected
        else ExternalFailureCapitalProtectionCondition.NOT_DEMONSTRATED
    )
    assert result.capital_protection_qualification.condition is expected


def test_structurally_equal_but_distinct_failure_is_rejected(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    structurally_equal = recognize_external_failure(failure.supporting_evidence)
    assert structurally_equal == failure
    assert structurally_equal is not failure

    with pytest.raises(ExecutionDomainError):
        publish_external_failure(
            failure, _qualification(structurally_equal, protected=False)
        )


def test_qualification_for_different_failure_is_rejected(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    other_failure = _failure(target)
    with pytest.raises(ExecutionDomainError):
        publish_external_failure(failure, _qualification(other_failure, protected=True))


def test_invalid_source_types_are_rejected(target: PortfolioState) -> None:
    failure = _failure(target)
    qualification = _qualification(failure, protected=False)
    with pytest.raises(ExecutionDomainError):
        publish_external_failure(object(), qualification)  # type: ignore[arg-type]
    with pytest.raises(ExecutionDomainError):
        publish_external_failure(failure, object())  # type: ignore[arg-type]


def test_publication_is_exact_immutable_and_preserves_source_contracts(
    target: PortfolioState,
) -> None:
    failure = _failure(target)
    qualification = _qualification(failure, protected=True)
    failure_evidence = failure.supporting_evidence
    qualification_evidence = qualification.supporting_evidence

    result = publish_external_failure(failure, qualification)

    assert [field.name for field in fields(result)] == [
        "external_failure",
        "capital_protection_qualification",
    ]
    forbidden = (
        "publication_id",
        "published_at",
        "failure_class",
        "condition",
        "supporting_evidence",
        "authority",
        "basis_reference",
        "context",
        "current_publication",
        "latest_publication",
    )
    assert not any(hasattr(result, name) for name in forbidden)
    assert failure.supporting_evidence == failure_evidence
    assert qualification.supporting_evidence == qualification_evidence
    with pytest.raises(FrozenInstanceError):
        result.external_failure = failure  # type: ignore[misc]


def test_direct_construction_is_rejected() -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalFailurePublication()
    with pytest.raises(ExecutionDomainError):
        ExternalFailurePublication(object(), object())  # type: ignore[call-arg]
