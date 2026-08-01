"""Append-only in-memory registries for lifecycle records."""

from typing import Generic, TypeVar

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationLifecycleIdError,
    InvalidPublicationLifecycleRecordError,
    PublicationLifecycleNotFoundError,
)
from quant_platform.strategy_evaluation.lifecycle.records import (
    PublishedStrategyEvaluationComparisonLifecycleRecord,
    PublishedStrategyEvaluationLifecycleRecord,
)


Record = TypeVar(
    "Record",
    PublishedStrategyEvaluationLifecycleRecord,
    PublishedStrategyEvaluationComparisonLifecycleRecord,
)


class _LifecycleRegistry(Generic[Record]):
    """Shared append-only storage mechanics with two atomic indexes."""

    _record_type: type[Record]

    def __init__(self) -> None:
        self._by_lifecycle_id: dict[str, Record] = {}
        self._by_publication_id: dict[str, list[Record]] = {}

    def append(self, record: Record) -> Record:
        """Append one exact record instance, rolling back partial index updates."""
        if not isinstance(record, self._record_type):
            raise InvalidPublicationLifecycleRecordError(
                f"Only {self._record_type.__name__} instances can be appended."
            )
        if self.exists(record.lifecycle_id):
            raise DuplicatePublicationLifecycleIdError(
                f"Lifecycle '{record.lifecycle_id}' is already registered."
            )
        self._by_lifecycle_id[record.lifecycle_id] = record
        history = self._by_publication_id.get(record.publication_id)
        created_history = history is None
        try:
            if history is None:
                history = []
                self._by_publication_id[record.publication_id] = history
            history.append(record)
        except Exception:
            del self._by_lifecycle_id[record.lifecycle_id]
            if created_history and record.publication_id in self._by_publication_id:
                del self._by_publication_id[record.publication_id]
            raise
        return record

    def get(self, lifecycle_id: str) -> Record:
        try:
            return self._by_lifecycle_id[lifecycle_id]
        except KeyError as error:
            raise PublicationLifecycleNotFoundError(
                f"Unknown publication lifecycle '{lifecycle_id}'."
            ) from error

    def exists(self, lifecycle_id: str) -> bool:
        return isinstance(lifecycle_id, str) and lifecycle_id in self._by_lifecycle_id

    def has_lifecycle(self, publication_id: str) -> bool:
        return (
            isinstance(publication_id, str)
            and publication_id in self._by_publication_id
            and bool(self._by_publication_id[publication_id])
        )

    def get_current(self, publication_id: str) -> Record:
        history = self.history(publication_id)
        return history[-1]

    def history(self, publication_id: str) -> tuple[Record, ...]:
        try:
            return tuple(self._by_publication_id[publication_id])
        except KeyError as error:
            raise PublicationLifecycleNotFoundError(
                f"Publication '{publication_id}' has no registered lifecycle."
            ) from error

    def list(self) -> tuple[Record, ...]:
        return tuple(self._by_lifecycle_id.values())


class PublishedStrategyEvaluationLifecycleRegistry(
    _LifecycleRegistry[PublishedStrategyEvaluationLifecycleRecord]
):
    """Append-only lifecycle registry for published strategy evaluations."""

    _record_type = PublishedStrategyEvaluationLifecycleRecord


class PublishedStrategyEvaluationComparisonLifecycleRegistry(
    _LifecycleRegistry[PublishedStrategyEvaluationComparisonLifecycleRecord]
):
    """Append-only lifecycle registry for published strategy comparisons."""

    _record_type = PublishedStrategyEvaluationComparisonLifecycleRecord
