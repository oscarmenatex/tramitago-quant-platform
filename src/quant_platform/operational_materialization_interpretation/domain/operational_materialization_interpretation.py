"""Quantitative interpretation of recognized operational materializations."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from quant_platform.execution import InvestmentOperation
from quant_platform.operational_materialization import OperationalMaterialization

from .exceptions import OperationalMaterializationInterpretationDomainError


def _validate_unique_occurrences(
    sources: tuple[OperationalMaterialization, ...],
) -> None:
    if len({source.occurrence_id for source in sources}) != len(sources):
        raise OperationalMaterializationInterpretationDomainError(
            "Every source must represent a distinct material occurrence."
        )


@dataclass(frozen=True, slots=True)
class OperationalMaterializationInterpretation:
    """Immutable materialized magnitude derived from explicit source facts."""

    operation: InvestmentOperation
    materialized_quantity: Decimal
    source_materializations: tuple[OperationalMaterialization, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.operation, InvestmentOperation):
            raise OperationalMaterializationInterpretationDomainError(
                "Interpretation requires one public InvestmentOperation."
            )
        if not isinstance(self.source_materializations, tuple):
            raise OperationalMaterializationInterpretationDomainError(
                "Interpretation provenance must be an immutable tuple."
            )
        if not self.source_materializations:
            raise OperationalMaterializationInterpretationDomainError(
                "Interpretation requires one or more materializations."
            )
        if not all(
            isinstance(source, OperationalMaterialization)
            for source in self.source_materializations
        ):
            raise OperationalMaterializationInterpretationDomainError(
                "Every source must be an OperationalMaterialization."
            )
        if not all(
            source.operation is self.operation
            for source in self.source_materializations
        ):
            raise OperationalMaterializationInterpretationDomainError(
                "Every materialization must correspond to the interpreted operation."
            )
        _validate_unique_occurrences(self.source_materializations)
        if not isinstance(self.materialized_quantity, Decimal):
            raise OperationalMaterializationInterpretationDomainError(
                "Materialized quantity must be an exact Decimal."
            )

        derived_quantity = sum(
            (source.quantity for source in self.source_materializations),
            start=Decimal("0"),
        )
        if self.materialized_quantity != derived_quantity:
            raise OperationalMaterializationInterpretationDomainError(
                "Materialized quantity must equal the joint source quantity."
            )


def interpret_materializations(
    operation: InvestmentOperation,
    materializations: Iterable[OperationalMaterialization],
) -> OperationalMaterializationInterpretation:
    """Interpret all supplied materializations for exactly one operation."""
    if not isinstance(operation, InvestmentOperation):
        raise OperationalMaterializationInterpretationDomainError(
            "Interpretation requires one public InvestmentOperation."
        )

    try:
        sources = tuple(materializations)
    except (TypeError, RuntimeError) as error:
        raise OperationalMaterializationInterpretationDomainError(
            "Interpretation requires one or more materializations."
        ) from error

    if not sources:
        raise OperationalMaterializationInterpretationDomainError(
            "Interpretation requires one or more materializations."
        )
    if not all(isinstance(source, OperationalMaterialization) for source in sources):
        raise OperationalMaterializationInterpretationDomainError(
            "Every source must be an OperationalMaterialization."
        )
    if not all(source.operation is operation for source in sources):
        raise OperationalMaterializationInterpretationDomainError(
            "Every materialization must correspond to the interpreted operation."
        )
    _validate_unique_occurrences(sources)

    materialized_quantity = sum(
        (source.quantity for source in sources), start=Decimal("0")
    )
    return OperationalMaterializationInterpretation(
        operation=operation,
        materialized_quantity=materialized_quantity,
        source_materializations=sources,
    )
