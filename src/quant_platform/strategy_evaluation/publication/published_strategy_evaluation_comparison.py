"""Immutable public projection of registered comparison evidence."""

from dataclasses import dataclass

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidPublishedStrategyEvaluationComparisonError,
)
from quant_platform.strategy_evaluation.domain.value_objects import ComparisonResult


@dataclass(frozen=True, slots=True)
class PublishedStrategyEvaluationComparison:
    """Self-contained, read-only public representation of one comparison."""

    publication_id: str
    comparison_id: str
    baseline_evaluation_id: str
    candidate_evaluation_ids: tuple[str, ...]
    comparison_method_id: str
    comparison_method_version: str
    result: ComparisonResult

    def __post_init__(self) -> None:
        for label, value in (
            ("Publication identity", self.publication_id),
            ("Comparison identity", self.comparison_id),
            ("Baseline evaluation identity", self.baseline_evaluation_id),
            ("Comparison method identity", self.comparison_method_id),
            ("Comparison method version", self.comparison_method_version),
        ):
            self._require_identifier(value, label)
        if not isinstance(self.candidate_evaluation_ids, tuple):
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "Candidate evaluation identities must be a tuple."
            )
        if not self.candidate_evaluation_ids:
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "A published comparison must contain at least one candidate."
            )
        for candidate_id in self.candidate_evaluation_ids:
            self._require_identifier(candidate_id, "Candidate evaluation identity")
        if self.baseline_evaluation_id in self.candidate_evaluation_ids:
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "The baseline evaluation cannot be a candidate evaluation."
            )
        if len(self.candidate_evaluation_ids) != len(set(self.candidate_evaluation_ids)):
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "Candidate evaluation identities must be unique."
            )
        if not isinstance(self.result, ComparisonResult):
            raise InvalidPublishedStrategyEvaluationComparisonError(
                "Result must be a valid ComparisonResult instance."
            )

    @staticmethod
    def _require_identifier(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidPublishedStrategyEvaluationComparisonError(
                f"{label} must be a non-empty string."
            )
