"""Public contract error for the Operational Request capability."""


class OperationalRequestDomainError(ValueError):
    """Raised when an Operational Request contract cannot be represented."""


__all__ = ["OperationalRequestDomainError"]
