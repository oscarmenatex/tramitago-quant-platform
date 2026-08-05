"""Orchestration for publishing registered comparison evidence."""

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationIdError,
    InvalidPublicationRequestError,
    PublicationProjectionError,
    StrategyEvaluationComparisonAlreadyPublishedError,
)
from quant_platform.strategy_evaluation.publication import (
    PublishedStrategyEvaluationComparison,
    StrategyEvaluationComparisonPublicationRegistry,
)
from quant_platform.strategy_evaluation.registry import StrategyEvaluationComparisonAccess


class StrategyEvaluationComparisonPublicationService:
    """Project one registered comparison into immutable public evidence."""

    def __init__(
        self,
        publication_registry: StrategyEvaluationComparisonPublicationRegistry,
        strategy_evaluation_comparison_access: StrategyEvaluationComparisonAccess,
    ) -> None:
        self._publication_registry = publication_registry
        self._strategy_evaluation_comparison_access = (
            strategy_evaluation_comparison_access
        )

    def publish(
        self, *, publication_id: str, comparison_id: str
    ) -> PublishedStrategyEvaluationComparison:
        """Create and atomically register a public projection of a comparison."""
        self._validate_request(publication_id, comparison_id)
        if self._publication_registry.exists(publication_id):
            raise DuplicatePublicationIdError(
                f"Publication '{publication_id}' is already registered."
            )
        if self._publication_registry.is_published(comparison_id):
            raise StrategyEvaluationComparisonAlreadyPublishedError(
                f"Comparison '{comparison_id}' is already published."
            )
        source = self._strategy_evaluation_comparison_access.get(comparison_id)
        publication = self._project(publication_id, source)
        return self._publication_registry.register(publication)

    @staticmethod
    def _validate_request(publication_id: object, comparison_id: object) -> None:
        if any(
            not isinstance(value, str) or not value.strip()
            for value in (publication_id, comparison_id)
        ):
            raise InvalidPublicationRequestError(
                "Publication and comparison identities must be non-empty strings."
            )

    @staticmethod
    def _project(
        publication_id: str, source: object
    ) -> PublishedStrategyEvaluationComparison:
        try:
            return PublishedStrategyEvaluationComparison(
                publication_id=publication_id,
                comparison_id=source.id,
                baseline_evaluation_id=source.baseline_evaluation_id,
                candidate_evaluation_ids=source.candidate_evaluation_ids,
                comparison_method_id=source.comparison_method_id,
                comparison_method_version=source.comparison_method_version,
                result=source.result,
            )
        except Exception as error:
            raise PublicationProjectionError(
                "Comparison could not be projected as public evidence."
            ) from error
