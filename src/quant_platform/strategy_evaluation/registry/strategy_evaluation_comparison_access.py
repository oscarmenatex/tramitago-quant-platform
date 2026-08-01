"""Read-only internal access boundary for registered comparisons."""

from quant_platform.strategy_evaluation.domain.entities import StrategyEvaluationComparison
from quant_platform.strategy_evaluation.registry.strategy_evaluation_comparison_registry import (
    StrategyEvaluationComparisonRegistry,
)


class StrategyEvaluationComparisonAccess:
    """Delegate read-only comparison queries to the internal registry."""

    def __init__(self, registry: StrategyEvaluationComparisonRegistry) -> None:
        self._registry = registry

    def get(self, comparison_id: str) -> StrategyEvaluationComparison:
        """Return one registered comparison."""
        return self._registry.get(comparison_id)

    def exists(self, comparison_id: str) -> bool:
        """Return whether a comparison has been registered."""
        return self._registry.exists(comparison_id)

    def list(self) -> tuple[StrategyEvaluationComparison, ...]:
        """Return an immutable snapshot of registered comparisons."""
        return self._registry.list()
