"""Replaceable evaluation-calculation contract."""

from collections.abc import Mapping
from typing import Any, Protocol

from quant_platform.strategy_evaluation.domain.entities import Strategy
from quant_platform.strategy_evaluation.domain.value_objects import (
    EvaluationContext,
    EvaluationCriteria,
)


class StrategyEvaluator(Protocol):
    """Produce a result without registering or interpreting an evaluation."""

    def evaluate(
        self,
        *,
        strategy: Strategy,
        context: EvaluationContext,
        criteria: EvaluationCriteria,
        knowledge: object,
    ) -> Mapping[str, Any]:
        """Return a deterministic, non-empty evaluation result."""
