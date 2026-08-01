"""In-memory registry for StrategyEvaluationComparison assets."""

from quant_platform.strategy_evaluation.domain.entities import StrategyEvaluationComparison
from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicateStrategyEvaluationComparisonError,
    StrategyEvaluationComparisonNotFoundError,
)


class StrategyEvaluationComparisonRegistry:
    """Register each immutable comparison exactly once."""

    def __init__(self) -> None:
        self._comparisons: dict[str, StrategyEvaluationComparison] = {}

    def register(self, comparison: StrategyEvaluationComparison) -> StrategyEvaluationComparison:
        """Store and return the same accepted comparison instance."""
        if self.exists(comparison.comparison_id):
            raise DuplicateStrategyEvaluationComparisonError(
                f"Comparison '{comparison.comparison_id}' is already registered."
            )
        self._comparisons[comparison.comparison_id] = comparison
        return comparison

    def get(self, comparison_id: str) -> StrategyEvaluationComparison:
        """Return a registered comparison by its identity."""
        try:
            return self._comparisons[comparison_id]
        except KeyError as error:
            raise StrategyEvaluationComparisonNotFoundError(
                f"Unknown comparison '{comparison_id}'."
            ) from error

    def exists(self, comparison_id: str) -> bool:
        """Return whether a comparison identity is registered."""
        return isinstance(comparison_id, str) and comparison_id in self._comparisons

    def list(self) -> tuple[StrategyEvaluationComparison, ...]:
        """Return an immutable snapshot in registration order."""
        return tuple(self._comparisons.values())
