"""Immutable technical evidence produced by a comparison."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidComparisonResultError,
)
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Value object for a non-decisional, structured comparison result."""

    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.values, Mapping) or not self.values:
            raise InvalidComparisonResultError(
                "Comparison result values must be a non-empty mapping."
            )
        if any(not isinstance(key, str) or not key.strip() for key in self.values):
            raise InvalidComparisonResultError(
                "Comparison result keys must be non-empty strings."
            )
        object.__setattr__(self, "values", freeze(self.values))
