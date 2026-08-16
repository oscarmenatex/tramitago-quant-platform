"""Public error raised during operational materialization recognition."""


class OperationalMaterializationDomainError(RuntimeError):
    """The Operational Materialization contract could not be satisfied."""


__all__ = ["OperationalMaterializationDomainError"]
