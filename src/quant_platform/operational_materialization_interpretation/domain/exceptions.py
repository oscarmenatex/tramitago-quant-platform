"""Public error for Operational Materialization Interpretation."""


class OperationalMaterializationInterpretationDomainError(RuntimeError):
    """The interpretation contract could not be satisfied."""


__all__ = ["OperationalMaterializationInterpretationDomainError"]
