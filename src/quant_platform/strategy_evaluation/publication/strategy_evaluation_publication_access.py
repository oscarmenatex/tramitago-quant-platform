"""Public read-only boundary for evaluation publications."""

from quant_platform.strategy_evaluation.publication.published_strategy_evaluation import (
    PublishedStrategyEvaluation,
)
from quant_platform.strategy_evaluation.publication.strategy_evaluation_publication_registry import (
    StrategyEvaluationPublicationRegistry,
)


class StrategyEvaluationPublicationAccess:
    """Delegate public read-only publication queries to the registry."""

    def __init__(self, registry: StrategyEvaluationPublicationRegistry) -> None:
        self._registry = registry

    def get(self, publication_id: str) -> PublishedStrategyEvaluation:
        return self._registry.get(publication_id)

    def resolve(self, evaluation_id: str) -> PublishedStrategyEvaluation:
        return self._registry.resolve(evaluation_id)

    def exists(self, publication_id: str) -> bool:
        return self._registry.exists(publication_id)

    def is_published(self, evaluation_id: str) -> bool:
        return self._registry.is_published(evaluation_id)

    def list(self) -> tuple[PublishedStrategyEvaluation, ...]:
        return self._registry.list()
