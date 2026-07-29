"""Exceptions raised when Strategy Evaluation domain invariants are violated."""


class StrategyEvaluationDomainError(ValueError):
    """Base exception for violations of Strategy Evaluation domain invariants."""


class InvalidStrategyError(StrategyEvaluationDomainError):
    """Raised when a Strategy definition is invalid."""


class InvalidEvaluationContextError(StrategyEvaluationDomainError):
    """Raised when an EvaluationContext does not describe a valid context."""


class InconsistentStrategyEvaluationError(StrategyEvaluationDomainError):
    """Raised when a StrategyEvaluation cannot be traced consistently."""


class InvalidEvaluationCriteriaError(StrategyEvaluationDomainError):
    """Raised when EvaluationCriteria contains an invalid characterization."""
