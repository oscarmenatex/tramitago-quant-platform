"""In-memory registry for immutable StrategyEvaluation assets."""

from quant_platform.strategy_evaluation.domain.entities import StrategyEvaluation
from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicateStrategyEvaluationError,
    InvalidEvaluationInputError,
)


class StrategyEvaluationRegistry:
    """Register each immutable evaluation exactly once."""

    def __init__(self) -> None:
        self._evaluations: dict[str, StrategyEvaluation] = {}

    def register(self, evaluation: StrategyEvaluation) -> StrategyEvaluation:
        """Store and return the accepted evaluation instance."""
        if not isinstance(evaluation, StrategyEvaluation):
            raise InvalidEvaluationInputError(
                "Only StrategyEvaluation instances can be registered."
            )
        if self.exists(evaluation.evaluation_id):
            raise DuplicateStrategyEvaluationError(
                f"Evaluation '{evaluation.evaluation_id}' is already registered."
            )
        self._evaluations[evaluation.evaluation_id] = evaluation
        return evaluation

    def get(self, evaluation_id: str) -> StrategyEvaluation:
        """Return one registered evaluation."""
        try:
            return self._evaluations[evaluation_id]
        except KeyError as error:
            raise KeyError(f"Unknown evaluation '{evaluation_id}'.") from error

    def exists(self, evaluation_id: str) -> bool:
        """Return whether an evaluation identity is already registered."""
        return isinstance(evaluation_id, str) and evaluation_id in self._evaluations

    def list(self) -> tuple[StrategyEvaluation, ...]:
        """Return an immutable snapshot of registered evaluations."""
        return tuple(self._evaluations.values())
