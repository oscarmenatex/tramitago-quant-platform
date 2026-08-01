"""Orchestrate the creation of traceable comparison evidence."""

from collections.abc import Mapping

from quant_platform.strategy_evaluation.domain.entities import (
    StrategyEvaluation,
    StrategyEvaluationComparison,
)
from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicateStrategyEvaluationComparisonError,
    IncompatibleEvaluationContextError,
    IncompatibleEvaluationCriteriaError,
    IncompatibleEvaluationResultError,
    IncompatibleKnowledgeReferenceError,
    InvalidComparisonRequestError,
    InvalidComparisonResultError,
    StrategyEvaluationComparisonExecutionError,
    StrategyEvaluationDomainError,
)
from quant_platform.strategy_evaluation.domain.ports import StrategyEvaluationComparator
from quant_platform.strategy_evaluation.domain.value_objects import ComparisonResult
from quant_platform.strategy_evaluation.registry import (
    StrategyEvaluationAccess,
    StrategyEvaluationComparisonRegistry,
)


class StrategyEvaluationComparisonService:
    """Validate, calculate, and atomically register a comparison."""

    def __init__(
        self,
        comparator: StrategyEvaluationComparator,
        registry: StrategyEvaluationComparisonRegistry,
        strategy_evaluation_access: StrategyEvaluationAccess,
    ) -> None:
        self._comparator = comparator
        self._registry = registry
        self._strategy_evaluation_access = strategy_evaluation_access

    def compare(
        self,
        *,
        comparison_id: str,
        baseline_evaluation_id: str,
        candidate_evaluation_ids: tuple[str, ...],
        comparison_method_id: str,
        comparison_method_version: str,
    ) -> StrategyEvaluationComparison:
        """Build and register evidence from compatible, registered evaluations."""
        self._validate_request(
            comparison_id,
            baseline_evaluation_id,
            candidate_evaluation_ids,
            comparison_method_id,
            comparison_method_version,
        )
        if self._registry.exists(comparison_id):
            raise DuplicateStrategyEvaluationComparisonError(
                f"Comparison '{comparison_id}' is already registered."
            )
        baseline = self._resolve_evaluation(baseline_evaluation_id)
        candidates = tuple(
            self._resolve_evaluation(evaluation_id)
            for evaluation_id in candidate_evaluation_ids
        )
        self._validate_comparability(baseline, candidates)
        result = self._compare(
            baseline, candidates, comparison_method_id, comparison_method_version
        )
        if not isinstance(result, ComparisonResult):
            raise InvalidComparisonResultError(
                "Strategy evaluation comparator must return ComparisonResult."
            )
        comparison = StrategyEvaluationComparison(
            comparison_id=comparison_id,
            baseline_evaluation_id=baseline.evaluation_id,
            candidate_evaluation_ids=tuple(
                candidate.evaluation_id for candidate in candidates
            ),
            comparison_method_id=comparison_method_id,
            comparison_method_version=comparison_method_version,
            result=result,
        )
        return self._registry.register(comparison)

    @staticmethod
    def _validate_request(
        comparison_id: object,
        baseline_evaluation_id: object,
        candidate_evaluation_ids: object,
        comparison_method_id: object,
        comparison_method_version: object,
    ) -> None:
        values = {
            "Comparison identity": comparison_id,
            "Baseline evaluation identity": baseline_evaluation_id,
            "Comparison method identity": comparison_method_id,
            "Comparison method version": comparison_method_version,
        }
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise InvalidComparisonRequestError(
                "Comparison identity, baseline, method, and version must be non-empty strings."
            )
        if not isinstance(candidate_evaluation_ids, tuple) or not candidate_evaluation_ids:
            raise InvalidComparisonRequestError(
                "Candidate evaluation identities must be a non-empty tuple."
            )
        if any(
            not isinstance(evaluation_id, str) or not evaluation_id.strip()
            for evaluation_id in candidate_evaluation_ids
        ):
            raise InvalidComparisonRequestError(
                "Candidate evaluation identities must be non-empty strings."
            )
        if baseline_evaluation_id in candidate_evaluation_ids:
            raise InvalidComparisonRequestError(
                "The baseline evaluation cannot be a candidate evaluation."
            )
        if len(candidate_evaluation_ids) != len(set(candidate_evaluation_ids)):
            raise InvalidComparisonRequestError(
                "Candidate evaluation identities must be unique."
            )

    def _resolve_evaluation(self, evaluation_id: str) -> StrategyEvaluation:
        return self._strategy_evaluation_access.get(evaluation_id)

    @staticmethod
    def _validate_comparability(
        baseline: StrategyEvaluation, candidates: tuple[StrategyEvaluation, ...]
    ) -> None:
        for candidate in candidates:
            if candidate.context != baseline.context:
                raise IncompatibleEvaluationContextError(
                    "Evaluations must share the same EvaluationContext."
                )
            if candidate.strategy.criteria != baseline.strategy.criteria:
                raise IncompatibleEvaluationCriteriaError(
                    "Evaluations must share equivalent EvaluationCriteria."
                )
            if (candidate.knowledge_id, candidate.knowledge_version) != (
                baseline.knowledge_id,
                baseline.knowledge_version,
            ):
                raise IncompatibleKnowledgeReferenceError(
                    "Evaluations must share the exact Knowledge reference."
                )
            if not isinstance(candidate.result, Mapping) or not candidate.result:
                raise IncompatibleEvaluationResultError(
                    "Each evaluation result must be a non-empty mapping."
                )
            if set(candidate.result) != set(baseline.result):
                raise IncompatibleEvaluationResultError(
                    "Evaluations must expose the same top-level result fields."
                )

    def _compare(
        self,
        baseline: StrategyEvaluation,
        candidates: tuple[StrategyEvaluation, ...],
        comparison_method_id: str,
        comparison_method_version: str,
    ) -> ComparisonResult:
        try:
            return self._comparator.compare(
                baseline=baseline,
                candidates=candidates,
                comparison_method_id=comparison_method_id,
                comparison_method_version=comparison_method_version,
            )
        except StrategyEvaluationDomainError:
            raise
        except Exception as error:
            raise StrategyEvaluationComparisonExecutionError(
                "Strategy evaluation comparator failed to produce a result."
            ) from error
