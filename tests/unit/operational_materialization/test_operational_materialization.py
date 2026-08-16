from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_materialization import (
    OperationalMaterialization,
    OperationalMaterializationBoundary,
    OperationalMaterializationDomainError,
    OperationalMaterializationObservation,
    recognize_materialization,
)


class StaticBoundary:
    def __init__(self, observation: object) -> None:
        self.observation = observation
        self.admissions: list[OperationalAdmission] = []

    def observe(self, admission: OperationalAdmission) -> object:
        self.admissions.append(admission)
        return self.observation


def _observation(
    admission: OperationalAdmission,
    occurrence_id: str = "occurrence-1",
) -> OperationalMaterializationObservation:
    return OperationalMaterializationObservation(
        occurrence_id=occurrence_id,
        operation=admission.submission.operational_request.operations[0],
        quantity=Decimal("0.5"),
        price=Decimal("12.34"),
        currency=CurrencyReference("USD"),
    )


def test_recognizes_valid_observation_and_preserves_all_values(
    admission: OperationalAdmission,
) -> None:
    observation = _observation(admission)
    boundary = StaticBoundary(observation)

    materialization = recognize_materialization(admission, boundary)  # type: ignore[arg-type]

    assert isinstance(materialization, OperationalMaterialization)
    assert boundary.admissions == [admission]
    assert materialization.occurrence_id is observation.occurrence_id
    assert materialization.operation is observation.operation
    assert materialization.quantity is observation.quantity
    assert materialization.price is observation.price
    assert materialization.currency is observation.currency


@pytest.mark.parametrize("price", [Decimal("0"), Decimal("-12.34")])
def test_finite_price_is_not_rejected_only_for_not_being_positive(
    admission: OperationalAdmission, price: Decimal
) -> None:
    operation = admission.submission.operational_request.operations[0]
    observation = OperationalMaterializationObservation(
        occurrence_id="finite-price",
        operation=operation,
        quantity=Decimal("0.5"),
        price=price,
        currency=CurrencyReference("USD"),
    )

    materialization = recognize_materialization(admission, StaticBoundary(observation))  # type: ignore[arg-type]

    assert materialization is not None
    assert materialization.operation is operation
    assert materialization.price is price


def test_normal_absence_returns_none(admission: OperationalAdmission) -> None:
    assert recognize_materialization(admission, StaticBoundary(None)) is None  # type: ignore[arg-type]


def test_rejected_admission_preserves_external_materialization_truth(
    admission: OperationalAdmission,
) -> None:
    rejected = OperationalAdmission(admission.submission, AdmissionDecision.REJECTED)
    observation = _observation(rejected, "rejected-occurrence")
    boundary = StaticBoundary(observation)

    materialization = recognize_materialization(rejected, boundary)  # type: ignore[arg-type]

    assert materialization is not None
    assert materialization.occurrence_id is observation.occurrence_id
    assert materialization.operation is observation.operation
    assert materialization.quantity is observation.quantity
    assert materialization.price is observation.price
    assert materialization.currency is observation.currency
    assert rejected.decision is AdmissionDecision.REJECTED
    assert boundary.admissions == [rejected]


def test_rejected_admission_with_normal_absence_returns_none(
    admission: OperationalAdmission,
) -> None:
    rejected = OperationalAdmission(admission.submission, AdmissionDecision.REJECTED)

    assert recognize_materialization(rejected, StaticBoundary(None)) is None  # type: ignore[arg-type]
    assert rejected.decision is AdmissionDecision.REJECTED


def test_operation_outside_admitted_flow_is_rejected(
    admission: OperationalAdmission,
) -> None:
    foreign = InvestmentOperation(
        InstrumentReference("FIGI", "FOREIGN"),
        OperationDirection.BUY,
        Decimal("1"),
    )
    observation = OperationalMaterializationObservation(
        "foreign-occurrence",
        foreign,
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(admission, StaticBoundary(observation))  # type: ignore[arg-type]


def test_equal_copy_of_admitted_operation_is_not_part_of_the_flow(
    admission: OperationalAdmission,
) -> None:
    original = admission.submission.operational_request.operations[0]
    copied = InvestmentOperation(
        original.instrument,
        original.direction,
        original.quantity,
    )
    assert copied == original
    assert copied is not original
    observation = OperationalMaterializationObservation(
        "copied-operation",
        copied,
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(admission, StaticBoundary(observation))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("attribute", "invalid"),
    [
        ("operation", object()),
        ("quantity", Decimal("0")),
        ("quantity", Decimal("NaN")),
        ("quantity", 1),
        ("price", Decimal("Infinity")),
        ("price", 10),
        ("currency", "USD"),
    ],
)
def test_incompatible_evidence_is_rejected(
    admission: OperationalAdmission, attribute: str, invalid: object
) -> None:
    values = {
        "occurrence_id": "valid-occurrence",
        "operation": admission.submission.operational_request.operations[0],
        "quantity": Decimal("1"),
        "price": Decimal("10"),
        "currency": CurrencyReference("USD"),
    }
    values[attribute] = invalid
    observation = OperationalMaterializationObservation(**values)  # type: ignore[arg-type]

    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(admission, StaticBoundary(observation))  # type: ignore[arg-type]


def test_boundary_failure_is_translated_to_the_single_public_error(
    admission: OperationalAdmission,
) -> None:
    class ProviderFailure(Exception):
        pass

    class FailingBoundary:
        def observe(self, admission: OperationalAdmission) -> None:
            raise ProviderFailure("private technical failure")

    with pytest.raises(OperationalMaterializationDomainError) as captured:
        recognize_materialization(admission, FailingBoundary())

    assert isinstance(captured.value.__cause__, ProviderFailure)


def test_boundary_must_return_observation_or_none(
    admission: OperationalAdmission,
) -> None:
    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(admission, StaticBoundary(object()))  # type: ignore[arg-type]


def test_distinct_boundaries_are_substitutable(
    admission: OperationalAdmission,
) -> None:
    observation = _observation(admission)

    class ComputedBoundary:
        def observe(
            self, admission: OperationalAdmission
        ) -> OperationalMaterializationObservation:
            return _observation(admission)

    static: OperationalMaterializationBoundary = StaticBoundary(observation)  # type: ignore[assignment]
    assert recognize_materialization(admission, static) == recognize_materialization(
        admission, ComputedBoundary()
    )


def test_multiple_occurrences_are_independent_and_immutable(
    admission: OperationalAdmission,
) -> None:
    first = recognize_materialization(
        admission, StaticBoundary(_observation(admission))
    )  # type: ignore[arg-type]
    second_observation = OperationalMaterializationObservation(
        "occurrence-2",
        admission.submission.operational_request.operations[0],
        Decimal("0.25"),
        Decimal("12.50"),
        CurrencyReference("USD"),
    )
    second = recognize_materialization(admission, StaticBoundary(second_observation))  # type: ignore[arg-type]

    assert first is not None and second is not None
    assert first.occurrence_id == "occurrence-1"
    assert second.occurrence_id == "occurrence-2"
    assert first.operation is second.operation
    assert first.quantity == Decimal("0.5")
    assert second.quantity == Decimal("0.25")
    assert not hasattr(first, "cumulative_quantity")
    assert not hasattr(first, "remaining_quantity")
    assert not hasattr(first, "average_price")
    assert not hasattr(first, "completion_state")
    with pytest.raises((FrozenInstanceError, AttributeError)):
        first.quantity = Decimal("2")  # type: ignore[misc]


def test_public_assets_are_contractually_minimal() -> None:
    expected = ["occurrence_id", "operation", "quantity", "price", "currency"]
    assert [item.name for item in fields(OperationalMaterialization)] == expected
    assert [
        item.name for item in fields(OperationalMaterializationObservation)
    ] == expected


def test_occurrence_identity_distinguishes_economically_equal_facts(
    admission: OperationalAdmission,
) -> None:
    first = recognize_materialization(
        admission,
        StaticBoundary(_observation(admission, "occurrence-a")),
    )
    second = recognize_materialization(
        admission,
        StaticBoundary(_observation(admission, "occurrence-b")),
    )
    same_occurrence = recognize_materialization(
        admission,
        StaticBoundary(_observation(admission, "occurrence-a")),
    )

    assert first is not None and second is not None and same_occurrence is not None
    assert first != second
    assert first == same_occurrence
    assert first.occurrence_id != second.occurrence_id


@pytest.mark.parametrize("invalid", [None, "", "   ", 1, object()])
def test_occurrence_identity_must_be_a_non_empty_string(
    admission: OperationalAdmission,
    invalid: object,
) -> None:
    observation = OperationalMaterializationObservation(
        invalid,  # type: ignore[arg-type]
        admission.submission.operational_request.operations[0],
        Decimal("1"),
        Decimal("10"),
        CurrencyReference("USD"),
    )

    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(admission, StaticBoundary(observation))  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid", [None, object(), "admission"])
def test_recognition_rejects_incompatible_preceding_input(invalid: object) -> None:
    with pytest.raises(OperationalMaterializationDomainError):
        recognize_materialization(invalid, StaticBoundary(None))  # type: ignore[arg-type]
