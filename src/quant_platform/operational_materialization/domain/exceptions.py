"""Public error raised by the Operational Materialization capability."""


class OperationalMaterializationDomainError(RuntimeError):
    """The Operational Materialization contract could not be satisfied."""


__all__ = ["OperationalMaterializationDomainError"]
