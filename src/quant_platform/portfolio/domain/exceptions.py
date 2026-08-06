class PortfolioStateError(ValueError):
    """Base error for a structurally invalid Portfolio State."""


class InvalidPortfolioComponentError(PortfolioStateError):
    """Raised when a position or monetary balance is invalid."""


class DuplicatePortfolioComponentError(PortfolioStateError):
    """Raised when an instrument or currency occurs more than once."""


class InvalidPortfolioTraceabilityError(PortfolioStateError):
    """Raised when public Portfolio traceability is incomplete or incoherent."""


__all__ = [
    "DuplicatePortfolioComponentError",
    "InvalidPortfolioComponentError",
    "InvalidPortfolioTraceabilityError",
    "PortfolioStateError",
]
