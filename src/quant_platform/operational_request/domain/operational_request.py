"""Immutable request formalized from one complete operational intent."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from quant_platform.execution import InvestmentOperation, OperationalIntent

from .exceptions import OperationalRequestDomainError


@dataclass(frozen=True, slots=True, init=False)
class OperationalRequest:
    """A complete request authorized by formalizing one operational intent."""

    operational_intent: OperationalIntent
    operations: tuple[InvestmentOperation, ...]

    def __init__(
        self,
        operational_intent: OperationalIntent,
        operations: Iterable[InvestmentOperation] | None = None,
    ) -> None:
        if not isinstance(operational_intent, OperationalIntent):
            raise OperationalRequestDomainError(
                "OperationalRequest requires one public OperationalIntent."
            )

        candidate = (
            operational_intent.operations
            if operations is None
            else self._validated_tuple(operations)
        )
        if Counter(candidate) != Counter(operational_intent.operations):
            raise OperationalRequestDomainError(
                "OperationalRequest operations must preserve all and only the "
                "operations of its OperationalIntent."
            )

        object.__setattr__(self, "operational_intent", operational_intent)
        object.__setattr__(self, "operations", candidate)

    @staticmethod
    def _validated_tuple(
        operations: Iterable[InvestmentOperation],
    ) -> tuple[InvestmentOperation, ...]:
        if isinstance(operations, (str, bytes)):
            raise OperationalRequestDomainError(
                "OperationalRequest operations must be InvestmentOperation values."
            )
        try:
            candidate = tuple(operations)
        except TypeError as error:
            raise OperationalRequestDomainError(
                "OperationalRequest operations must be iterable."
            ) from error
        if not all(isinstance(item, InvestmentOperation) for item in candidate):
            raise OperationalRequestDomainError(
                "OperationalRequest operations must be InvestmentOperation values."
            )
        return candidate
