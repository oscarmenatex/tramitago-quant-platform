class PortfolioStateError(ValueError):
    """Base error for a structurally invalid Portfolio State."""


class InvalidPortfolioComponentError(PortfolioStateError):
    """Raised when a position or monetary balance is invalid."""


class DuplicatePortfolioComponentError(PortfolioStateError):
    """Raised when an instrument or currency occurs more than once."""


class InvalidPortfolioTraceabilityError(PortfolioStateError):
    """Raised when public Portfolio traceability is incomplete or incoherent."""


class PortfolioTargetDeterminationError(PortfolioStateError):
    """Base error for contractual Target Determination failures."""


class InvalidPortfolioTargetInputError(PortfolioTargetDeterminationError):
    """Current state or Risk candidates are invalid."""


class InvalidPortfolioTargetAuthorityError(PortfolioTargetDeterminationError):
    """The supplied determination authority is invalid."""


class InvalidPortfolioTargetCompositionError(PortfolioTargetDeterminationError):
    """The authority produced an invalid target composition."""


__all__ = [
    "DuplicatePortfolioComponentError",
    "InvalidPortfolioComponentError",
    "InvalidPortfolioTraceabilityError",
    "InvalidPortfolioTargetAuthorityError",
    "InvalidPortfolioTargetCompositionError",
    "InvalidPortfolioTargetInputError",
    "PortfolioTargetDeterminationError",
    "PortfolioStateError",
]
