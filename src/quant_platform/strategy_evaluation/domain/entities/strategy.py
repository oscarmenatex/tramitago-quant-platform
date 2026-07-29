"""Strategy entity."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quant_platform.strategy_evaluation.domain.exceptions import InvalidStrategyError
from quant_platform.strategy_evaluation.domain.value_objects import EvaluationCriteria
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze


@dataclass(frozen=True)
class Strategy:
    """Immutable formal specification of an investment methodology."""

    strategy_id: str
    definition: Mapping[str, Any]
    criteria: EvaluationCriteria

    def __post_init__(self) -> None:
        if not isinstance(self.strategy_id, str) or not self.strategy_id.strip():
            raise InvalidStrategyError("Strategy identity must be a non-empty string.")
        if not isinstance(self.definition, Mapping) or not self.definition:
            raise InvalidStrategyError("Strategy definition must be a non-empty mapping.")
        if any(not isinstance(key, str) or not key.strip() for key in self.definition):
            raise InvalidStrategyError("Strategy definition keys must be non-empty strings.")
        if not isinstance(self.criteria, EvaluationCriteria):
            raise InvalidStrategyError("Strategy criteria must be EvaluationCriteria.")
        object.__setattr__(self, "definition", freeze(self.definition))

    @property
    def id(self) -> str:
        """Return the Strategy identity."""
        return self.strategy_id
