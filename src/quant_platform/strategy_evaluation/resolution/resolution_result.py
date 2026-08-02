"""Immutable public output contract for publication resolution."""

from dataclasses import dataclass

from quant_platform.strategy_evaluation.domain.exceptions import InvalidResolutionResultError
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation import (
    PublishedStrategyEvaluation,
)
from quant_platform.strategy_evaluation.publication.published_strategy_evaluation_comparison import (
    PublishedStrategyEvaluationComparison,
)


PublishedPublication = (
    PublishedStrategyEvaluation | PublishedStrategyEvaluationComparison
)


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    """The complete, immutable result of one successful resolution."""

    publication: PublishedPublication

    def __post_init__(self) -> None:
        if not isinstance(
            self.publication,
            (PublishedStrategyEvaluation, PublishedStrategyEvaluationComparison),
        ):
            raise InvalidResolutionResultError(
                "Result must contain exactly one published public projection."
            )

    @property
    def publication_id(self) -> str:
        """Expose the resolved public identity without duplicating the projection."""
        return self.publication.publication_id

    def __hash__(self) -> int:
        """Keep the public value hashable even when a projection holds mappings."""
        return hash((type(self.publication), self.publication_id))
