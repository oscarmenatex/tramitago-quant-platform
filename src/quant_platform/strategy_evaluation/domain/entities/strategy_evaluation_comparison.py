"""Immutable asset representing a comparison of StrategyEvaluation records."""

from dataclasses import dataclass

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidStrategyEvaluationComparisonError,
)
from quant_platform.strategy_evaluation.domain.value_objects import ComparisonResult


@dataclass(frozen=True, slots=True)
class StrategyEvaluationComparison:
    """Traceable evidence from comparing one baseline with ordered candidates."""

    comparison_id: str
    baseline_evaluation_id: str
    candidate_evaluation_ids: tuple[str, ...]
    comparison_method_id: str
    comparison_method_version: str
    result: ComparisonResult

    def __post_init__(self) -> None:
        self._require_identifier(self.comparison_id, "Comparison identity")
        self._require_identifier(self.baseline_evaluation_id, "Baseline evaluation identity")
        self._require_identifier(self.comparison_method_id, "Comparison method identity")
        self._require_identifier(
            self.comparison_method_version, "Comparison method version"
        )
        if not isinstance(self.candidate_evaluation_ids, tuple):
            raise InvalidStrategyEvaluationComparisonError(
                "Candidate evaluation identities must be a tuple."
            )
        if not self.candidate_evaluation_ids:
            raise InvalidStrategyEvaluationComparisonError(
                "A comparison must contain at least one candidate evaluation."
            )
        for candidate_id in self.candidate_evaluation_ids:
            self._require_identifier(candidate_id, "Candidate evaluation identity")
        if self.baseline_evaluation_id in self.candidate_evaluation_ids:
            raise InvalidStrategyEvaluationComparisonError(
                "The baseline evaluation cannot be a candidate evaluation."
            )
        if len(self.candidate_evaluation_ids) != len(set(self.candidate_evaluation_ids)):
            raise InvalidStrategyEvaluationComparisonError(
                "Candidate evaluation identities must be unique."
            )
        if not isinstance(self.result, ComparisonResult):
            raise InvalidStrategyEvaluationComparisonError(
                "A comparison must contain a valid ComparisonResult."
            )

    @staticmethod
    def _require_identifier(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidStrategyEvaluationComparisonError(
                f"{label} must be a non-empty string."
            )

    @property
    def id(self) -> str:
        """Return the comparison identity."""
        return self.comparison_id
