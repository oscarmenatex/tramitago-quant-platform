from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone, tzinfo

import pytest

from quant_platform.execution import (
    ExecutionDomainError,
    ExternalFailure,
    ExternalFailureAuthority,
    ExternalFailureClass,
    ExternalFailureObligation,
    ExternalFailureReferenceTime,
    ReconciliationReferenceTime,
    SupportingExternalFailureEvidence,
    declare_required_reconciliation_scope,
    prepare_operational_request,
    recognize_external_failure,
)
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import PortfolioState


class IndeterminableTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def _contexts(target: PortfolioState) -> dict[ExternalFailureObligation, object]:
    request = prepare_operational_request(target)
    submission = OperationalSubmission(request)
    admission = OperationalAdmission(submission, AdmissionDecision.ADMITTED)
    scope = declare_required_reconciliation_scope(
        ReconciliationReferenceTime(datetime(2026, 8, 21, tzinfo=timezone.utc))
    )
    return {
        ExternalFailureObligation.OPERATIONAL_PRESENTATION: request,
        ExternalFailureObligation.ADMISSION_OBSERVATION: submission,
        ExternalFailureObligation.MATERIALIZATION_OBSERVATION: admission,
        ExternalFailureObligation.ORDER_TERMINAL_OBSERVATION: submission,
        ExternalFailureObligation.RECONCILIATION_EVIDENCE_OBSERVATION: scope,
    }


def _evidence(
    context: object,
    obligation: ExternalFailureObligation,
    *,
    authority: str = "opaque authority",
    failure_class: ExternalFailureClass = ExternalFailureClass.INTERACTION_FAILURE,
    reference_time: datetime | None = None,
    observed_at_utc: datetime | None = None,
) -> SupportingExternalFailureEvidence:
    return SupportingExternalFailureEvidence(
        authority=ExternalFailureAuthority(authority),
        obligation=obligation,
        failure_class=failure_class,
        reference_time=ExternalFailureReferenceTime(
            reference_time or datetime(2026, 8, 21, 12, tzinfo=timezone.utc)
        ),
        observed_at_utc=observed_at_utc
        or datetime(2026, 8, 21, 12, 1, tzinfo=timezone.utc),
        context=context,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("obligation", tuple(ExternalFailureObligation))
def test_each_obligation_accepts_exact_context_and_preserves_it(
    target: PortfolioState, obligation: ExternalFailureObligation
) -> None:
    context = _contexts(target)[obligation]
    failure = recognize_external_failure((_evidence(context, obligation),))
    assert failure.obligation is obligation
    assert failure.context is context


@pytest.mark.parametrize("obligation", tuple(ExternalFailureObligation))
def test_each_obligation_rejects_a_mismatched_context(
    target: PortfolioState, obligation: ExternalFailureObligation
) -> None:
    contexts = _contexts(target)
    wrong = next(value for key, value in contexts.items() if key is not obligation)
    with pytest.raises(ExecutionDomainError):
        _evidence(wrong, obligation)


@pytest.mark.parametrize("failure_class", tuple(ExternalFailureClass))
def test_recognizes_both_failure_classes(
    target: PortfolioState, failure_class: ExternalFailureClass
) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    failure = recognize_external_failure(
        (
            _evidence(
                context,
                ExternalFailureObligation.OPERATIONAL_PRESENTATION,
                failure_class=failure_class,
            ),
        )
    )
    assert failure.failure_class is failure_class


def test_evidence_rejects_a_failure_class_outside_enum(target: PortfolioState) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    with pytest.raises(ExecutionDomainError):
        _evidence(
            context,
            ExternalFailureObligation.OPERATIONAL_PRESENTATION,
            failure_class="INTERACTION_FAILURE",  # type: ignore[arg-type]
        )


def test_recognition_requires_one_or_more_evidence() -> None:
    with pytest.raises(ExecutionDomainError):
        recognize_external_failure(())


def test_repeated_same_instance_is_one_semantic_element(
    target: PortfolioState,
) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    evidence = _evidence(
        context, ExternalFailureObligation.OPERATIONAL_PRESENTATION
    )
    failure = recognize_external_failure((evidence, evidence, evidence))
    assert failure.supporting_evidence == (evidence,)
    assert failure.supporting_evidence[0] is evidence


def test_distinct_compatible_evidence_are_all_preserved_by_identity(
    target: PortfolioState,
) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    first = _evidence(context, ExternalFailureObligation.OPERATIONAL_PRESENTATION)
    second = _evidence(
        context,
        ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        observed_at_utc=datetime(2026, 8, 21, 12, 2, tzinfo=timezone.utc),
    )
    failure = recognize_external_failure((first, second))
    assert len(failure.supporting_evidence) == 2
    assert failure.supporting_evidence[0] is first
    assert failure.supporting_evidence[1] is second


@pytest.mark.parametrize(
    "difference",
    ["authority", "obligation", "failure_class", "reference_time"],
)
def test_incompatible_evidence_is_rejected(
    target: PortfolioState, difference: str
) -> None:
    contexts = _contexts(target)
    context = contexts[ExternalFailureObligation.ADMISSION_OBSERVATION]
    first = _evidence(context, ExternalFailureObligation.ADMISSION_OBSERVATION)
    kwargs: dict[str, object] = {}
    obligation = ExternalFailureObligation.ADMISSION_OBSERVATION
    if difference == "authority":
        kwargs["authority"] = "different authority"
    elif difference == "obligation":
        obligation = ExternalFailureObligation.ORDER_TERMINAL_OBSERVATION
    elif difference == "failure_class":
        kwargs["failure_class"] = ExternalFailureClass.EVIDENCE_FAILURE
    else:
        kwargs["reference_time"] = datetime(
            2026, 8, 21, 12, 0, 1, tzinfo=timezone.utc
        )
    second = _evidence(context, obligation, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ExecutionDomainError):
        recognize_external_failure((first, second))


def test_structurally_equal_but_distinct_context_is_rejected(
    target: PortfolioState,
) -> None:
    first_context = prepare_operational_request(target)
    second_context = prepare_operational_request(target)
    assert first_context == second_context
    assert first_context is not second_context
    with pytest.raises(ExecutionDomainError):
        recognize_external_failure(
            (
                _evidence(
                    first_context,
                    ExternalFailureObligation.OPERATIONAL_PRESENTATION,
                ),
                _evidence(
                    second_context,
                    ExternalFailureObligation.OPERATIONAL_PRESENTATION,
                ),
            )
        )


def test_equivalent_reference_instants_with_different_offsets_are_compatible(
    target: PortfolioState,
) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    first = _evidence(
        context,
        ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        reference_time=datetime(2026, 8, 21, 12, tzinfo=timezone.utc),
    )
    second = _evidence(
        context,
        ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        reference_time=datetime(
            2026, 8, 21, 8, tzinfo=timezone(timedelta(hours=-4))
        ),
    )
    assert len(recognize_external_failure((first, second)).supporting_evidence) == 2


def test_temporal_values_require_contractual_offsets(target: PortfolioState) -> None:
    with pytest.raises(ExecutionDomainError):
        ExternalFailureReferenceTime(datetime(2026, 8, 21))
    with pytest.raises(ExecutionDomainError):
        ExternalFailureReferenceTime(
            datetime(2026, 8, 21, tzinfo=IndeterminableTimezone())
        )
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    with pytest.raises(ExecutionDomainError):
        _evidence(
            context,
            ExternalFailureObligation.OPERATIONAL_PRESENTATION,
            observed_at_utc=datetime(
                2026, 8, 21, 13, tzinfo=timezone(timedelta(hours=1))
            ),
        )


def test_contracts_are_exact_immutable_and_controlled(target: PortfolioState) -> None:
    context = _contexts(target)[ExternalFailureObligation.OPERATIONAL_PRESENTATION]
    evidence = _evidence(
        context, ExternalFailureObligation.OPERATIONAL_PRESENTATION
    )
    failure = recognize_external_failure((evidence,))
    assert [item.name for item in fields(SupportingExternalFailureEvidence)] == [
        "authority",
        "obligation",
        "failure_class",
        "reference_time",
        "observed_at_utc",
        "context",
    ]
    assert [item.name for item in fields(ExternalFailure)] == [
        "obligation",
        "failure_class",
        "context",
        "supporting_evidence",
    ]
    with pytest.raises(ExecutionDomainError):
        ExternalFailure()
    with pytest.raises((FrozenInstanceError, AttributeError)):
        failure.context = object()  # type: ignore[misc]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        evidence.context = object()  # type: ignore[misc]


def test_authority_is_non_empty_opaque_and_immutable() -> None:
    authority = ExternalFailureAuthority(" provider-specific:opaque/value ")
    assert authority.value == " provider-specific:opaque/value "
    for invalid in ("", "   ", None, 42):
        with pytest.raises(ExecutionDomainError):
            ExternalFailureAuthority(invalid)  # type: ignore[arg-type]
    with pytest.raises((FrozenInstanceError, AttributeError)):
        authority.value = "changed"  # type: ignore[misc]


def test_enums_are_exhaustive() -> None:
    assert tuple(ExternalFailureClass) == (
        ExternalFailureClass.INTERACTION_FAILURE,
        ExternalFailureClass.EVIDENCE_FAILURE,
    )
    assert tuple(ExternalFailureObligation) == (
        ExternalFailureObligation.OPERATIONAL_PRESENTATION,
        ExternalFailureObligation.ADMISSION_OBSERVATION,
        ExternalFailureObligation.MATERIALIZATION_OBSERVATION,
        ExternalFailureObligation.ORDER_TERMINAL_OBSERVATION,
        ExternalFailureObligation.RECONCILIATION_EVIDENCE_OBSERVATION,
    )
