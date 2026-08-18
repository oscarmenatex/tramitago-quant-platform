"""Public API for materialization interpretation within Execution."""

from .domain import (
    OperationalMaterializationInterpretation,
    OperationalMaterializationInterpretationDomainError,
    interpret_materializations,
)

__all__ = [
    "OperationalMaterializationInterpretation",
    "interpret_materializations",
    "OperationalMaterializationInterpretationDomainError",
]
