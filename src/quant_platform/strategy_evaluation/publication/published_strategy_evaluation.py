"""Immutable public projection of registered StrategyEvaluation evidence."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidPublishedStrategyEvaluationError,
)
from quant_platform.strategy_evaluation.domain.value_objects import (
    EvaluationContext,
    EvaluationCriteria,
)
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze


@dataclass(frozen=True, slots=True)
class PublishedStrategyEvaluation:
    """Self-contained, read-only public representation of one evaluation."""

    publication_id: str
    evaluation_id: str
    strategy_id: str
    knowledge_id: str
    knowledge_version: str
    context: EvaluationContext
    criteria: EvaluationCriteria
    result: Mapping[str, Any]

    def __post_init__(self) -> None:
        for label, value in (
            ("Publication identity", self.publication_id),
            ("Evaluation identity", self.evaluation_id),
            ("Strategy identity", self.strategy_id),
            ("Knowledge identity", self.knowledge_id),
            ("Knowledge version", self.knowledge_version),
        ):
            self._require_identifier(value, label)
        if not isinstance(self.context, EvaluationContext):
            raise InvalidPublishedStrategyEvaluationError(
                "Context must be a valid EvaluationContext instance."
            )
        if not isinstance(self.criteria, EvaluationCriteria):
            raise InvalidPublishedStrategyEvaluationError(
                "Criteria must be a valid EvaluationCriteria instance."
            )
        if not isinstance(self.result, Mapping) or not self.result:
            raise InvalidPublishedStrategyEvaluationError(
                "Published evaluation result must be a non-empty mapping."
            )
        if any(not isinstance(key, str) or not key.strip() for key in self.result):
            raise InvalidPublishedStrategyEvaluationError(
                "Published evaluation result keys must be non-empty strings."
            )
        object.__setattr__(self, "result", freeze(self.result))

    @staticmethod
    def _require_identifier(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidPublishedStrategyEvaluationError(
                f"{label} must be a non-empty string."
            )
