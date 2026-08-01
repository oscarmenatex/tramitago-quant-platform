"""Replaceable contract for the technical comparison calculation."""

from typing import Protocol

from quant_platform.strategy_evaluation.domain.entities import StrategyEvaluation
from quant_platform.strategy_evaluation.domain.value_objects import ComparisonResult


class StrategyEvaluationComparator(Protocol):
    """Calculate evidence for compatible evaluations without side effects."""

    def compare(
        self,
        *,
        baseline: StrategyEvaluation,
        candidates: tuple[StrategyEvaluation, ...],
        comparison_method_id: str,
        comparison_method_version: str,
    ) -> ComparisonResult:
        """Return deterministic comparison evidence."""
