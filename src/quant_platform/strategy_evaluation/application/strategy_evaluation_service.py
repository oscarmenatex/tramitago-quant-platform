"""Orchestration for producing a traceable StrategyEvaluation."""

from collections.abc import Mapping
from typing import Any

from quant_platform.research.knowledge.consumption import KnowledgeConsumptionAccess
from quant_platform.strategy_evaluation.domain.entities import Strategy, StrategyEvaluation
from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicateStrategyEvaluationError,
    InvalidEvaluationIdentityError,
    InvalidEvaluationInputError,
    InvalidEvaluationResultError,
    KnowledgeNotFoundError,
    StrategyEvaluatorExecutionError,
)
from quant_platform.strategy_evaluation.domain.ports import StrategyEvaluator
from quant_platform.strategy_evaluation.domain.value_objects import (
    EvaluationContext,
    EvaluationCriteria,
)
from quant_platform.strategy_evaluation.registry import StrategyEvaluationRegistry


class StrategyEvaluationService:
    """Validate, calculate, and atomically register one evaluation."""

    def __init__(
        self,
        evaluator: StrategyEvaluator,
        registry: StrategyEvaluationRegistry,
        knowledge_access: KnowledgeConsumptionAccess,
    ) -> None:
        self._evaluator = evaluator
        self._registry = registry
        self._knowledge_access = knowledge_access

    def evaluate(
        self,
        *,
        evaluation_id: str,
        strategy: Strategy,
        context: EvaluationContext,
        criteria: EvaluationCriteria,
        knowledge_id: str,
        knowledge_version: str,
    ) -> StrategyEvaluation:
        """Produce and register an evaluation from explicit, immutable inputs."""
        self._validate_inputs(
            evaluation_id, strategy, context, criteria, knowledge_id, knowledge_version
        )
        if self._registry.exists(evaluation_id):
            raise DuplicateStrategyEvaluationError(
                f"Evaluation '{evaluation_id}' is already registered."
            )

        knowledge = self._resolve_knowledge(knowledge_id, knowledge_version)
        result = self._evaluate(strategy, context, criteria, knowledge)
        self._validate_result(result)

        evaluation = StrategyEvaluation(
            evaluation_id=evaluation_id,
            strategy=strategy,
            context=context,
            knowledge_id=knowledge_id,
            knowledge_version=knowledge_version,
            result=result,
        )
        return self._registry.register(evaluation)

    def _validate_inputs(
        self,
        evaluation_id: object,
        strategy: object,
        context: object,
        criteria: object,
        knowledge_id: object,
        knowledge_version: object,
    ) -> None:
        if not isinstance(evaluation_id, str) or not evaluation_id.strip():
            raise InvalidEvaluationIdentityError(
                "Evaluation identity must be a non-empty string."
            )
        if not isinstance(knowledge_id, str) or not knowledge_id.strip():
            raise InvalidEvaluationInputError("Knowledge identity must be a non-empty string.")
        if not isinstance(knowledge_version, str) or not knowledge_version.strip():
            raise InvalidEvaluationInputError("Knowledge version must be a non-empty string.")
        if not isinstance(strategy, Strategy):
            raise InvalidEvaluationInputError("Strategy must be a valid Strategy instance.")
        if not isinstance(context, EvaluationContext):
            raise InvalidEvaluationInputError(
                "Context must be a valid EvaluationContext instance."
            )
        if not isinstance(criteria, EvaluationCriteria):
            raise InvalidEvaluationInputError(
                "Criteria must be a valid EvaluationCriteria instance."
            )
        if strategy.criteria != criteria:
            raise InvalidEvaluationInputError(
                "Explicit criteria must match the criteria associated with Strategy."
            )

    def _resolve_knowledge(self, knowledge_id: str, knowledge_version: str) -> object:
        try:
            return self._knowledge_access.resolve(knowledge_id, knowledge_version)
        except Exception as error:
            raise KnowledgeNotFoundError(
                f"Published Knowledge '{knowledge_id}' version "
                f"'{knowledge_version}' could not be resolved."
            ) from error

    def _evaluate(
        self,
        strategy: Strategy,
        context: EvaluationContext,
        criteria: EvaluationCriteria,
        knowledge: object,
    ) -> Mapping[str, Any]:
        try:
            return self._evaluator.evaluate(
                strategy=strategy,
                context=context,
                criteria=criteria,
                knowledge=knowledge,
            )
        except Exception as error:
            raise StrategyEvaluatorExecutionError(
                "Strategy evaluator failed to produce a result."
            ) from error

    def _validate_result(self, result: object) -> None:
        if not isinstance(result, Mapping) or not result:
            raise InvalidEvaluationResultError(
                "Strategy evaluator must return a non-empty mapping."
            )
