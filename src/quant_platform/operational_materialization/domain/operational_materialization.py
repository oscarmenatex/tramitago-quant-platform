"""Recognition of one material occurrence in an admitted operational flow."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from quant_platform.core import CurrencyReference
from quant_platform.execution import InvestmentOperation
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission

from .exceptions import OperationalMaterializationDomainError


@dataclass(frozen=True, slots=True)
class OperationalMaterializationObservation:
    """Normalized candidate evidence, before contractual recognition."""

    operation: InvestmentOperation
    quantity: Decimal
    price: Decimal
    currency: CurrencyReference


class OperationalMaterializationBoundary(Protocol):
    """Replaceable boundary that supplies normalized candidate evidence."""

    def observe(
        self, admission: OperationalAdmission
    ) -> OperationalMaterializationObservation | None:
        """Return one new candidate observation, or normal absence."""
        ...


@dataclass(frozen=True, slots=True)
class OperationalMaterialization:
    """Immutable recognized fact for one individual material occurrence."""

    operation: InvestmentOperation
    quantity: Decimal
    price: Decimal
    currency: CurrencyReference

    def __post_init__(self) -> None:
        _validate_evidence(self.operation, self.quantity, self.price, self.currency)


def _validate_evidence(
    operation: object,
    quantity: object,
    price: object,
    currency: object,
) -> None:
    if not isinstance(operation, InvestmentOperation):
        raise OperationalMaterializationDomainError(
            "Materialization requires one public InvestmentOperation."
        )
    if (
        not isinstance(quantity, Decimal)
        or not quantity.is_finite()
        or quantity <= 0
    ):
        raise OperationalMaterializationDomainError(
            "Materialization quantity must be an exact, finite, positive Decimal."
        )
    if not isinstance(price, Decimal) or not price.is_finite():
        raise OperationalMaterializationDomainError(
            "Materialization price must be an exact, finite Decimal."
        )
    if not isinstance(currency, CurrencyReference):
        raise OperationalMaterializationDomainError(
            "Materialization price requires one public CurrencyReference."
        )


def recognize_materialization(
    admission: OperationalAdmission,
    boundary: OperationalMaterializationBoundary,
) -> OperationalMaterialization | None:
    """Recognize one normalized occurrence in an admitted operational flow."""
    if not isinstance(admission, OperationalAdmission):
        raise OperationalMaterializationDomainError(
            "recognize_materialization requires one public OperationalAdmission."
        )
    if admission.decision is not AdmissionDecision.ADMITTED:
        raise OperationalMaterializationDomainError(
            "Only an ADMITTED operational flow can produce a materialization."
        )

    try:
        observation = boundary.observe(admission)
    except Exception as error:
        raise OperationalMaterializationDomainError(
            "A materialization observation could not be obtained."
        ) from error

    if observation is None:
        return None
    if not isinstance(observation, OperationalMaterializationObservation):
        raise OperationalMaterializationDomainError(
            "The boundary did not provide an OperationalMaterializationObservation."
        )

    _validate_evidence(
        observation.operation,
        observation.quantity,
        observation.price,
        observation.currency,
    )
    admitted_operations = (
        admission.submission.operational_request.operations
    )
    if not any(operation is observation.operation for operation in admitted_operations):
        raise OperationalMaterializationDomainError(
            "The observed operation does not belong to the admitted flow."
        )

    return OperationalMaterialization(
        operation=observation.operation,
        quantity=observation.quantity,
        price=observation.price,
        currency=observation.currency,
    )
