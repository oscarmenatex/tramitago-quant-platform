"""Public contract error for the Execution capability."""


class ExecutionDomainError(ValueError):
    """Raised when an Execution domain contract cannot be represented."""


__all__ = ["ExecutionDomainError"]
