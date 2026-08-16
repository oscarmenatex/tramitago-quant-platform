"""Domain contracts for materialization recognition within Execution."""

from .exceptions import OperationalMaterializationDomainError
from .operational_materialization import (
    OperationalMaterialization,
    OperationalMaterializationBoundary,
    OperationalMaterializationObservation,
    recognize_materialization,
)

__all__ = [
    "OperationalMaterialization",
    "OperationalMaterializationObservation",
    "OperationalMaterializationBoundary",
    "recognize_materialization",
    "OperationalMaterializationDomainError",
]
