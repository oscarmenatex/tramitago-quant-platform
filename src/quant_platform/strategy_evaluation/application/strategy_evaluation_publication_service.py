"""Orchestration for publishing registered StrategyEvaluation evidence."""

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationIdError,
    InvalidPublicationRequestError,
    PublicationProjectionError,
    StrategyEvaluationAlreadyPublishedError,
)
from quant_platform.strategy_evaluation.publication import (
    PublishedStrategyEvaluation,
    StrategyEvaluationPublicationRegistry,
)
from quant_platform.strategy_evaluation.registry import StrategyEvaluationAccess


class StrategyEvaluationPublicationService:
    """Project one registered evaluation into immutable public evidence."""

    def __init__(
        self,
        publication_registry: StrategyEvaluationPublicationRegistry,
        strategy_evaluation_access: StrategyEvaluationAccess,
    ) -> None:
        self._publication_registry = publication_registry
        self._strategy_evaluation_access = strategy_evaluation_access

    def publish(
        self, *, publication_id: str, evaluation_id: str
    ) -> PublishedStrategyEvaluation:
        """Create and atomically register a public projection of an evaluation."""
        self._validate_request(publication_id, evaluation_id)
        if self._publication_registry.exists(publication_id):
            raise DuplicatePublicationIdError(
                f"Publication '{publication_id}' is already registered."
            )
        if self._publication_registry.is_published(evaluation_id):
            raise StrategyEvaluationAlreadyPublishedError(
                f"Evaluation '{evaluation_id}' is already published."
            )
        source = self._strategy_evaluation_access.get(evaluation_id)
        publication = self._project(publication_id, source)
        return self._publication_registry.register(publication)

    @staticmethod
    def _validate_request(publication_id: object, evaluation_id: object) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (publication_id, evaluation_id)
        ):
            raise InvalidPublicationRequestError(
                "Publication and evaluation identities must be non-empty strings."
            )

    @staticmethod
    def _project(
        publication_id: str, source: object
    ) -> PublishedStrategyEvaluation:
        try:
            return PublishedStrategyEvaluation(
                publication_id=publication_id,
                evaluation_id=source.id,
                strategy_id=source.strategy.id,
                knowledge_id=source.knowledge_id,
                knowledge_version=source.knowledge_version,
                context=source.context,
                criteria=source.strategy.criteria,
                result=source.result,
            )
        except Exception as error:
            raise PublicationProjectionError(
                "Evaluation could not be projected as public evidence."
            ) from error
