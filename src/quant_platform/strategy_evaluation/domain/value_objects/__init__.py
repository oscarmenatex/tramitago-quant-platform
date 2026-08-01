"""Immutable value objects of the Strategy Evaluation domain."""

from quant_platform.strategy_evaluation.domain.value_objects.evaluation_context import (
    EvaluationContext,
)
from quant_platform.strategy_evaluation.domain.value_objects.evaluation_criteria import (
    EvaluationCriteria,
)
from quant_platform.strategy_evaluation.domain.value_objects.comparison_result import (
    ComparisonResult,
)

__all__ = ["ComparisonResult", "EvaluationContext", "EvaluationCriteria"]
