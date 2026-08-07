"""Public structural errors for Portfolio Transition."""


class PortfolioTransitionError(ValueError):
    """Base error for an invalid portfolio transition."""


class InvalidPortfolioTransitionComponentError(PortfolioTransitionError):
    """Raised when a constituent value is structurally invalid."""


class DuplicatePortfolioTransitionComponentError(PortfolioTransitionError):
    """Raised when a public identity occurs more than once."""


class InvalidPortfolioTransitionRelationError(PortfolioTransitionError):
    """Raised when declared changes do not relate the supplied states."""


__all__ = [
    "DuplicatePortfolioTransitionComponentError",
    "InvalidPortfolioTransitionComponentError",
    "InvalidPortfolioTransitionRelationError",
    "PortfolioTransitionError",
]
