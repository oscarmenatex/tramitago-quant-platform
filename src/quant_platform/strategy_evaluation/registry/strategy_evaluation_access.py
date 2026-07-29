"""Read-only internal access boundary for registered evaluations."""

from quant_platform.strategy_evaluation.domain.entities import StrategyEvaluation
from quant_platform.strategy_evaluation.registry.strategy_evaluation_registry import (
    StrategyEvaluationRegistry,
)


class StrategyEvaluationAccess:
    """Delegate read-only evaluation queries to the internal registry."""

    def __init__(self, registry: StrategyEvaluationRegistry) -> None:
        self._registry = registry

    def get(self, evaluation_id: str) -> StrategyEvaluation:
        """Return one registered evaluation."""
        return self._registry.get(evaluation_id)

    def exists(self, evaluation_id: str) -> bool:
        """Return whether an evaluation has been registered."""
        return self._registry.exists(evaluation_id)

    def list(self) -> tuple[StrategyEvaluation, ...]:
        """Return an immutable snapshot of registered evaluations."""
        return self._registry.list()
