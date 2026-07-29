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


class InvalidEvaluationIdentityError(StrategyEvaluationDomainError):
    """Raised when an evaluation identifier cannot identify an evaluation."""


class DuplicateStrategyEvaluationError(StrategyEvaluationDomainError):
    """Raised when an evaluation identifier has already been registered."""


class KnowledgeNotFoundError(StrategyEvaluationDomainError):
    """Raised when the requested published Knowledge cannot be resolved."""


class KnowledgeVersionMismatchError(StrategyEvaluationDomainError):
    """Raised when published Knowledge does not have the requested version."""


class InvalidEvaluationInputError(StrategyEvaluationDomainError):
    """Raised when a process input is not a valid domain object."""


class InvalidEvaluationResultError(StrategyEvaluationDomainError):
    """Raised when an evaluator returns an invalid result."""


class StrategyEvaluatorExecutionError(StrategyEvaluationDomainError):
    """Raised when an evaluator cannot complete its calculation."""
