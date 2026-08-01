"""Public read-only boundary for comparison publications."""

from quant_platform.strategy_evaluation.publication.published_strategy_evaluation_comparison import (
    PublishedStrategyEvaluationComparison,
)
from quant_platform.strategy_evaluation.publication.strategy_evaluation_comparison_publication_registry import (
    StrategyEvaluationComparisonPublicationRegistry,
)


class StrategyEvaluationComparisonPublicationAccess:
    """Delegate public read-only publication queries to the registry."""

    def __init__(self, registry: StrategyEvaluationComparisonPublicationRegistry) -> None:
        self._registry = registry

    def get(self, publication_id: str) -> PublishedStrategyEvaluationComparison:
        return self._registry.get(publication_id)

    def resolve(self, comparison_id: str) -> PublishedStrategyEvaluationComparison:
        return self._registry.resolve(comparison_id)

    def exists(self, publication_id: str) -> bool:
        return self._registry.exists(publication_id)

    def is_published(self, comparison_id: str) -> bool:
        return self._registry.is_published(comparison_id)

    def list(self) -> tuple[PublishedStrategyEvaluationComparison, ...]:
        return self._registry.list()
