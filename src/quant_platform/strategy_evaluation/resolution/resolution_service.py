"""Deterministic, read-only publication resolution application service."""

from quant_platform.strategy_evaluation.domain.exceptions import (
    AmbiguousPublicationResolutionError,
    PublicationLifecycleNotFoundError,
    PublicationNotFoundError,
    PublicationNotResolvableError,
)
from quant_platform.strategy_evaluation.lifecycle.access import (
    PublishedStrategyEvaluationComparisonLifecycleAccess,
    PublishedStrategyEvaluationLifecycleAccess,
)
from quant_platform.strategy_evaluation.lifecycle.records import PublicationLifecycleStatus
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation import (
    PublishedStrategyEvaluation,
)
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation_comparison import (
    PublishedStrategyEvaluationComparison,
)
from quant_platform.strategy_evaluation.publication.strategy_evaluation_comparison_publication_access import (
    StrategyEvaluationComparisonPublicationAccess,
)
from quant_platform.strategy_evaluation.publication.strategy_evaluation_publication_access import (
    StrategyEvaluationPublicationAccess,
)

from .resolution_context import PublicationResolutionKind, ResolutionContext
from .resolution_result import PublishedPublication, ResolutionResult


class StrategyEvaluationPublicationResolutionService:
    """Resolve one active public projection using only public read accesses."""

    def __init__(
        self,
        evaluation_publications: StrategyEvaluationPublicationAccess,
        comparison_publications: StrategyEvaluationComparisonPublicationAccess,
        evaluation_lifecycles: PublishedStrategyEvaluationLifecycleAccess,
        comparison_lifecycles: PublishedStrategyEvaluationComparisonLifecycleAccess,
    ) -> None:
        self._evaluation_publications = evaluation_publications
        self._comparison_publications = comparison_publications
        self._evaluation_lifecycles = evaluation_lifecycles
        self._comparison_lifecycles = comparison_lifecycles

    def resolve(self, context: ResolutionContext) -> ResolutionResult:
        """Return one active publication or raise a normative resolution error."""
        if not isinstance(context, ResolutionContext):
            raise TypeError("context must be a ResolutionContext.")
        if context.publication_kind is PublicationResolutionKind.EVALUATION:
            candidates = self._candidates(
                context.source_id,
                self._evaluation_publications,
                PublishedStrategyEvaluation,
                "evaluation_id",
            )
            lifecycle_access = self._evaluation_lifecycles
        else:
            candidates = self._candidates(
                context.source_id,
                self._comparison_publications,
                PublishedStrategyEvaluationComparison,
                "comparison_id",
            )
            lifecycle_access = self._comparison_lifecycles
        if not candidates:
            raise PublicationNotFoundError(
                f"No publication exists for source '{context.source_id}'."
            )
        resolvable = []
        lifecycle_found = False
        for candidate in candidates:
            if not lifecycle_access.has_lifecycle(candidate.publication_id):
                continue
            lifecycle_found = True
            lifecycle = lifecycle_access.get_current(candidate.publication_id)
            if lifecycle.status is PublicationLifecycleStatus.ACTIVE:
                resolvable.append(candidate)
        if not lifecycle_found:
            raise PublicationLifecycleNotFoundError(
                f"No candidate publication for '{context.source_id}' has a lifecycle."
            )
        if not resolvable:
            raise PublicationNotResolvableError(
                f"No candidate publication for '{context.source_id}' is active."
            )
        if len(resolvable) != 1:
            raise AmbiguousPublicationResolutionError(
                f"More than one active publication exists for source '{context.source_id}'."
            )
        return ResolutionResult(resolvable[0])

    @staticmethod
    def _candidates(
        source_id: str,
        access: object,
        publication_type: type[PublishedPublication],
        source_attribute: str,
    ) -> PublishedPublication:
        """Return every public projection in the canonical context."""
        publications = tuple(access.list())  # type: ignore[attr-defined]
        return [
            publication
            for publication in publications
            if isinstance(publication, publication_type)
            and getattr(publication, source_attribute) == source_id
        ]
