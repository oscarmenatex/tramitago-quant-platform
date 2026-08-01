"""Criteria used to characterize a strategy."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quant_platform.strategy_evaluation.domain.exceptions import InvalidEvaluationCriteriaError
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze


@dataclass(frozen=True)
class EvaluationCriteria:
    """Immutable, identity-free characterization criteria for a Strategy."""

    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping) or not self.values:
            raise InvalidEvaluationCriteriaError(
                "Evaluation criteria must be a non-empty mapping."
            )
        if any(not isinstance(key, str) or not key.strip() for key in self.values):
            raise InvalidEvaluationCriteriaError(
                "Evaluation criteria keys must be non-empty strings."
            )
        object.__setattr__(self, "values", freeze(self.values))

    @property
    def criteria(self) -> Mapping[str, Any]:
        """Return the immutable criteria mapping."""
        return self.values
