"""Public error raised during materialization interpretation in Execution."""


class OperationalMaterializationInterpretationDomainError(RuntimeError):
    """The interpretation contract could not be satisfied."""


__all__ = ["OperationalMaterializationInterpretationDomainError"]
