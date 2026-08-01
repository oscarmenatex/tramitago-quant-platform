"""Application services for Strategy Evaluation."""

from quant_platform.strategy_evaluation.application.strategy_evaluation_service import (
    StrategyEvaluationService,
)
from quant_platform.strategy_evaluation.application.strategy_evaluation_comparison_service import (
    StrategyEvaluationComparisonService,
)

__all__ = ["StrategyEvaluationService", "StrategyEvaluationComparisonService"]
