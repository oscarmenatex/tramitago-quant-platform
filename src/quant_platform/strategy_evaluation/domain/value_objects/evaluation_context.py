"""Value object describing the conditions of a strategy evaluation."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from quant_platform.strategy_evaluation.domain.exceptions import InvalidEvaluationContextError
from quant_platform.strategy_evaluation.domain.value_objects._frozen import freeze

_PeriodPoint = date | datetime


@dataclass(frozen=True)
class EvaluationContext:
    """Immutable conditions under which one Strategy is evaluated."""

    period_start: _PeriodPoint
    period_end: _PeriodPoint
    asset_universe: tuple[str, ...]
    temporal_horizon: str
    market_regime: str
    restrictions: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.period_start, (date, datetime)) or not isinstance(
            self.period_end, (date, datetime)
        ):
            raise InvalidEvaluationContextError("Evaluation period bounds must be dates.")
        try:
            period_is_invalid = self.period_start > self.period_end
        except TypeError as error:
            raise InvalidEvaluationContextError(
                "Evaluation period bounds must be comparable."
            ) from error
        if period_is_invalid:
            raise InvalidEvaluationContextError(
                "Evaluation period start cannot be after its end."
            )
        if not self.asset_universe or any(
            not isinstance(asset, str) or not asset.strip()
            for asset in self.asset_universe
        ):
            raise InvalidEvaluationContextError(
                "Asset universe must contain non-empty asset identifiers."
            )
        if not isinstance(self.temporal_horizon, str) or not self.temporal_horizon.strip():
            raise InvalidEvaluationContextError("Temporal horizon must be specified.")
        if not isinstance(self.market_regime, str) or not self.market_regime.strip():
            raise InvalidEvaluationContextError("Market regime must be specified.")
        if not isinstance(self.restrictions, Mapping):
            raise InvalidEvaluationContextError("Restrictions must be a mapping.")

        object.__setattr__(self, "asset_universe", tuple(self.asset_universe))
        object.__setattr__(self, "restrictions", freeze(self.restrictions))

    @property
    def evaluation_period(self) -> tuple[_PeriodPoint, _PeriodPoint]:
        """Return the inclusive conceptual evaluation period."""
        return self.period_start, self.period_end
