"""Read-only public boundaries for publication lifecycle queries."""

from quant_platform.strategy_evaluation.lifecycle.records import (
    PublishedStrategyEvaluationComparisonLifecycleRecord,
    PublishedStrategyEvaluationLifecycleRecord,
)
from quant_platform.strategy_evaluation.lifecycle.registries import (
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    PublishedStrategyEvaluationLifecycleRegistry,
)


class PublishedStrategyEvaluationLifecycleAccess:
    """Delegate lifecycle reads to the evaluation lifecycle registry."""

    def __init__(self, registry: PublishedStrategyEvaluationLifecycleRegistry) -> None:
        self._registry = registry

    def get(self, lifecycle_id: str) -> PublishedStrategyEvaluationLifecycleRecord:
        return self._registry.get(lifecycle_id)

    def exists(self, lifecycle_id: str) -> bool:
        return self._registry.exists(lifecycle_id)

    def has_lifecycle(self, publication_id: str) -> bool:
        return self._registry.has_lifecycle(publication_id)

    def get_current(self, publication_id: str) -> PublishedStrategyEvaluationLifecycleRecord:
        return self._registry.get_current(publication_id)

    def history(
        self, publication_id: str
    ) -> tuple[PublishedStrategyEvaluationLifecycleRecord, ...]:
        return self._registry.history(publication_id)

    def list(self) -> tuple[PublishedStrategyEvaluationLifecycleRecord, ...]:
        return self._registry.list()


class PublishedStrategyEvaluationComparisonLifecycleAccess:
    """Delegate lifecycle reads to the comparison lifecycle registry."""

    def __init__(
        self, registry: PublishedStrategyEvaluationComparisonLifecycleRegistry
    ) -> None:
        self._registry = registry

    def get(self, lifecycle_id: str) -> PublishedStrategyEvaluationComparisonLifecycleRecord:
        return self._registry.get(lifecycle_id)

    def exists(self, lifecycle_id: str) -> bool:
        return self._registry.exists(lifecycle_id)

    def has_lifecycle(self, publication_id: str) -> bool:
        return self._registry.has_lifecycle(publication_id)

    def get_current(
        self, publication_id: str
    ) -> PublishedStrategyEvaluationComparisonLifecycleRecord:
        return self._registry.get_current(publication_id)

    def history(
        self, publication_id: str
    ) -> tuple[PublishedStrategyEvaluationComparisonLifecycleRecord, ...]:
        return self._registry.history(publication_id)

    def list(self) -> tuple[PublishedStrategyEvaluationComparisonLifecycleRecord, ...]:
        return self._registry.list()
