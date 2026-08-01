"""StrategyEvaluation entity."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quant_platform.strategy_evaluation.domain.entities.strategy import Strategy
from quant_platform.strategy_evaluation.domain.exceptions import (
    InconsistentStrategyEvaluationError,
)
from quant_platform.strategy_evaluation.domain.value_objects import EvaluationContext
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze


@dataclass(frozen=True)
class StrategyEvaluation:
    """Immutable, traceable result of evaluating a Strategy in one context."""

    evaluation_id: str
    strategy: Strategy
    context: EvaluationContext
    knowledge_id: str
    knowledge_version: str
    result: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.evaluation_id, str) or not self.evaluation_id.strip():
            raise InconsistentStrategyEvaluationError(
                "Evaluation identity must be a non-empty string."
            )
        if not isinstance(self.strategy, Strategy):
            raise InconsistentStrategyEvaluationError(
                "A strategy evaluation must reference exactly one Strategy."
            )
        if not isinstance(self.context, EvaluationContext):
            raise InconsistentStrategyEvaluationError(
                "A strategy evaluation must reference exactly one EvaluationContext."
            )
        if not isinstance(self.knowledge_id, str) or not self.knowledge_id.strip():
            raise InconsistentStrategyEvaluationError(
                "A strategy evaluation must reference a knowledge identity."
            )
        if not isinstance(self.knowledge_version, str) or not self.knowledge_version.strip():
            raise InconsistentStrategyEvaluationError(
                "A strategy evaluation must reference a knowledge version."
            )
        object.__setattr__(self, "knowledge_id", self.knowledge_id.strip())
        object.__setattr__(self, "knowledge_version", self.knowledge_version.strip())
        if not isinstance(self.result, Mapping) or not self.result:
            raise InconsistentStrategyEvaluationError(
                "A strategy evaluation must contain a non-empty result."
            )
        object.__setattr__(self, "result", freeze(self.result))

    @property
    def id(self) -> str:
        """Return the StrategyEvaluation identity."""
        return self.evaluation_id
