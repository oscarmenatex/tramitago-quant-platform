"""Canonical, infrastructure-free Strategy Evaluation domain."""

from quant_platform.strategy_evaluation.domain.entities import Strategy, StrategyEvaluation
from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidEvaluationContextError,
    InvalidEvaluationCriteriaError,
    InvalidEvaluationIdentityError,
    InvalidEvaluationInputError,
    InvalidEvaluationResultError,
    InvalidStrategyError,
    InconsistentStrategyEvaluationError,
    DuplicateStrategyEvaluationError,
    KnowledgeNotFoundError,
    KnowledgeVersionMismatchError,
    StrategyEvaluatorExecutionError,
)
from quant_platform.strategy_evaluation.domain.value_objects import (
    EvaluationContext,
    EvaluationCriteria,
)

__all__ = [
    "EvaluationContext",
    "EvaluationCriteria",
    "InconsistentStrategyEvaluationError",
    "InvalidEvaluationContextError",
    "InvalidEvaluationCriteriaError",
    "InvalidEvaluationIdentityError",
    "InvalidEvaluationInputError",
    "InvalidEvaluationResultError",
    "InvalidStrategyError",
    "Strategy",
    "StrategyEvaluation",
    "DuplicateStrategyEvaluationError",
    "KnowledgeNotFoundError",
    "KnowledgeVersionMismatchError",
    "StrategyEvaluatorExecutionError",
]
