"""In-memory registry for published comparison projections."""

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationIdError,
    InvalidPublishedStrategyEvaluationComparisonError,
    PublishedStrategyEvaluationComparisonNotFoundError,
    StrategyEvaluationComparisonAlreadyPublishedError,
)
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation_comparison import (
    PublishedStrategyEvaluationComparison,
)


class StrategyEvaluationComparisonPublicationRegistry:
    """Register each comparison publication exactly once by both identities."""

    def __init__(self) -> None:
        self._by_publication_id: dict[str, PublishedStrategyEvaluationComparison] = {}
        self._by_comparison_id: dict[str, PublishedStrategyEvaluationComparison] = {}

    def register(
        self, publication: PublishedStrategyEvaluationComparison
    ) -> PublishedStrategyEvaluationComparison:
        if not isinstance(publication, PublishedStrategyEvaluationComparison):
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "Only PublishedStrategyEvaluationComparison instances can be registered."
            )
        if self.exists(publication.publication_id):
            raise DuplicatePublicationIdError(
                f"Publication '{publication.publication_id}' is already registered."
            )
        if self.is_published(publication.comparison_id):
            raise StrategyEvaluationComparisonAlreadyPublishedError(
                f"Comparison '{publication.comparison_id}' is already published."
            )
        self._by_publication_id[publication.publication_id] = publication
        try:
            self._by_comparison_id[publication.comparison_id] = publication
        except Exception:
            del self._by_publication_id[publication.publication_id]
            raise
        return publication

    def get(self, publication_id: str) -> PublishedStrategyEvaluationComparison:
        try:
            return self._by_publication_id[publication_id]
        except KeyError as error:
            raise PublishedStrategyEvaluationComparisonNotFoundError(
                f"Unknown comparison publication '{publication_id}'."
            ) from error

    def resolve(self, comparison_id: str) -> PublishedStrategyEvaluationComparison:
        try:
            return self._by_comparison_id[comparison_id]
        except KeyError as error:
            raise PublishedStrategyEvaluationComparisonNotFoundError(
                f"No publication exists for comparison '{comparison_id}'."
            ) from error

    def exists(self, publication_id: str) -> bool:
        return isinstance(publication_id, str) and publication_id in self._by_publication_id

    def is_published(self, comparison_id: str) -> bool:
        return isinstance(comparison_id, str) and comparison_id in self._by_comparison_id

    def list(self) -> tuple[PublishedStrategyEvaluationComparison, ...]:
        return tuple(self._by_publication_id.values())
