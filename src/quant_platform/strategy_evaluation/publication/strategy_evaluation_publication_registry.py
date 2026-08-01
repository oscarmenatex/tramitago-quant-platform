"""In-memory registry for published evaluation projections."""

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationIdError,
    InvalidPublishedStrategyEvaluationError,
    PublishedStrategyEvaluationNotFoundError,
    StrategyEvaluationAlreadyPublishedError,
)
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation import (
    PublishedStrategyEvaluation,
)


class StrategyEvaluationPublicationRegistry:
    """Register each evaluation publication exactly once by both identities."""

    def __init__(self) -> None:
        self._by_publication_id: dict[str, PublishedStrategyEvaluation] = {}
        self._by_evaluation_id: dict[str, PublishedStrategyEvaluation] = {}

    def register(self, publication: PublishedStrategyEvaluation) -> PublishedStrategyEvaluation:
        """Atomically store and return the exact accepted publication."""
        if not isinstance(publication, PublishedStrategyEvaluation):
            raise InvalidPublishedStrategyEvaluationError(
                "Only PublishedStrategyEvaluation instances can be registered."
            )
        if self.exists(publication.publication_id):
            raise DuplicatePublicationIdError(
                f"Publication '{publication.publication_id}' is already registered."
            )
        if self.is_published(publication.evaluation_id):
            raise StrategyEvaluationAlreadyPublishedError(
                f"Evaluation '{publication.evaluation_id}' is already published."
            )
        self._by_publication_id[publication.publication_id] = publication
        try:
            self._by_evaluation_id[publication.evaluation_id] = publication
        except Exception:
            del self._by_publication_id[publication.publication_id]
            raise
        return publication

    def get(self, publication_id: str) -> PublishedStrategyEvaluation:
        """Return one publication by public identity."""
        try:
            return self._by_publication_id[publication_id]
        except KeyError as error:
            raise PublishedStrategyEvaluationNotFoundError(
                f"Unknown evaluation publication '{publication_id}'."
            ) from error

    def resolve(self, evaluation_id: str) -> PublishedStrategyEvaluation:
        """Return one publication by its source evaluation identity."""
        try:
            return self._by_evaluation_id[evaluation_id]
        except KeyError as error:
            raise PublishedStrategyEvaluationNotFoundError(
                f"No publication exists for evaluation '{evaluation_id}'."
            ) from error

    def exists(self, publication_id: str) -> bool:
        return isinstance(publication_id, str) and publication_id in self._by_publication_id

    def is_published(self, evaluation_id: str) -> bool:
        return isinstance(evaluation_id, str) and evaluation_id in self._by_evaluation_id

    def list(self) -> tuple[PublishedStrategyEvaluation, ...]:
        return tuple(self._by_publication_id.values())
