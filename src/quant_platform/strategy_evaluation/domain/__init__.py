"""Canonical, infrastructure-free Strategy Evaluation domain."""

from quant_platform.strategy_evaluation.domain.entities import Strategy, StrategyEvaluation
from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidEvaluationContextError,
    InvalidEvaluationCriteriaError,
    InvalidStrategyError,
    InconsistentStrategyEvaluationError,
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
    "InvalidStrategyError",
    "Strategy",
    "StrategyEvaluation",
]
