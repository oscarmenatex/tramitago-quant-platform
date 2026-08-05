"""Authorized state transitions for immutable published evidence lifecycle."""

from datetime import datetime, timezone
from typing import Generic, TypeVar

from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationLifecycleIdError,
    InvalidPublicationLifecycleRecordError,
    InvalidPublicationLifecycleTransitionError,
    PublicationAlreadySupersededError,
    PublicationAlreadyWithdrawnError,
    PublicationLifecycleAlreadyRegisteredError,
    PublicationLifecycleCycleError,
    PublicationLifecycleNotFoundError,
    PublicationSuccessorLifecycleNotFoundError,
    PublicationSuccessorNotActiveError,
    PublicationSuccessorNotFoundError,
)
from quant_platform.strategy_evaluation.lifecycle.records import (
    PublicationLifecycleStatus,
    PublishedStrategyEvaluationComparisonLifecycleRecord,
    PublishedStrategyEvaluationLifecycleRecord,
)
from quant_platform.strategy_evaluation.lifecycle.registries import (
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    PublishedStrategyEvaluationLifecycleRegistry,
)
from quant_platform.strategy_evaluation.publication import (
    StrategyEvaluationComparisonPublicationAccess,
    StrategyEvaluationPublicationAccess,
)


Record = TypeVar(
    "Record",
    PublishedStrategyEvaluationLifecycleRecord,
    PublishedStrategyEvaluationComparisonLifecycleRecord,
)


class _PublicationLifecycleService(Generic[Record]):
    """Shared orchestration; subclasses bind one public publication contract."""

    _record_type: type[Record]

    def __init__(self, publication_access: object, registry: object) -> None:
        self._publication_access = publication_access
        self._registry = registry

    def register_initial(
        self,
        *,
        lifecycle_id: str,
        publication_id: str,
        transitioned_at: datetime,
    ) -> Record:
        self._validate_identifiers(lifecycle_id, publication_id)
        self._validate_timestamp(transitioned_at)
        if self._registry.exists(lifecycle_id):
            raise DuplicatePublicationLifecycleIdError(
                f"Lifecycle '{lifecycle_id}' is already registered."
            )
        self._publication_access.get(publication_id)
        if self._registry.has_lifecycle(publication_id):
            raise PublicationLifecycleAlreadyRegisteredError(
                f"Publication '{publication_id}' already has a lifecycle."
            )
        return self._registry.append(
            self._record_type(
                lifecycle_id=lifecycle_id,
                publication_id=publication_id,
                status=PublicationLifecycleStatus.ACTIVE,
                previous_lifecycle_id=None,
                successor_publication_id=None,
                transitioned_at=transitioned_at,
                reason=None,
            )
        )

    def supersede(
        self,
        *,
        lifecycle_id: str,
        publication_id: str,
        successor_publication_id: str,
        transitioned_at: datetime,
        reason: str,
    ) -> Record:
        self._validate_identifiers(lifecycle_id, publication_id, successor_publication_id)
        self._validate_timestamp(transitioned_at)
        self._validate_reason(reason)
        if self._registry.exists(lifecycle_id):
            raise DuplicatePublicationLifecycleIdError(
                f"Lifecycle '{lifecycle_id}' is already registered."
            )
        self._publication_access.get(publication_id)
        if not self._publication_access.exists(successor_publication_id):
            raise PublicationSuccessorNotFoundError(
                f"Successor publication '{successor_publication_id}' does not exist."
            )
        if publication_id == successor_publication_id:
            raise PublicationLifecycleCycleError(
                "A publication cannot succeed itself."
            )
        current = self._current_active(publication_id)
        if not self._registry.has_lifecycle(successor_publication_id):
            raise PublicationSuccessorLifecycleNotFoundError(
                f"Successor publication '{successor_publication_id}' has no lifecycle."
            )
        successor_current = self._registry.get_current(successor_publication_id)
        if successor_current.status is not PublicationLifecycleStatus.ACTIVE:
            raise PublicationSuccessorNotActiveError(
                f"Successor publication '{successor_publication_id}' is not active."
            )
        if self._would_create_cycle(publication_id, successor_publication_id):
            raise PublicationLifecycleCycleError(
                "The proposed successor would create a lifecycle cycle."
            )
        self._validate_monotonic_timestamp(transitioned_at, current.transitioned_at)
        return self._registry.append(
            self._record_type(
                lifecycle_id=lifecycle_id,
                publication_id=publication_id,
                status=PublicationLifecycleStatus.SUPERSEDED,
                previous_lifecycle_id=current.lifecycle_id,
                successor_publication_id=successor_publication_id,
                transitioned_at=transitioned_at,
                reason=reason,
            )
        )

    def withdraw(
        self,
        *,
        lifecycle_id: str,
        publication_id: str,
        transitioned_at: datetime,
        reason: str,
    ) -> Record:
        self._validate_identifiers(lifecycle_id, publication_id)
        self._validate_timestamp(transitioned_at)
        self._validate_reason(reason)
        if self._registry.exists(lifecycle_id):
            raise DuplicatePublicationLifecycleIdError(
                f"Lifecycle '{lifecycle_id}' is already registered."
            )
        self._publication_access.get(publication_id)
        current = self._current_active(publication_id)
        self._validate_monotonic_timestamp(transitioned_at, current.transitioned_at)
        return self._registry.append(
            self._record_type(
                lifecycle_id=lifecycle_id,
                publication_id=publication_id,
                status=PublicationLifecycleStatus.WITHDRAWN,
                previous_lifecycle_id=current.lifecycle_id,
                successor_publication_id=None,
                transitioned_at=transitioned_at,
                reason=reason,
            )
        )

    def _current_active(self, publication_id: str) -> Record:
        if not self._registry.has_lifecycle(publication_id):
            raise PublicationLifecycleNotFoundError(
                f"Publication '{publication_id}' has no registered lifecycle."
            )
        current = self._registry.get_current(publication_id)
        if current.status is PublicationLifecycleStatus.SUPERSEDED:
            raise PublicationAlreadySupersededError(
                f"Publication '{publication_id}' has already been superseded."
            )
        if current.status is PublicationLifecycleStatus.WITHDRAWN:
            raise PublicationAlreadyWithdrawnError(
                f"Publication '{publication_id}' has already been withdrawn."
            )
        if current.status is not PublicationLifecycleStatus.ACTIVE:
            raise InvalidPublicationLifecycleTransitionError(
                f"Publication '{publication_id}' is not active."
            )
        return current

    def _would_create_cycle(self, publication_id: str, successor_publication_id: str) -> bool:
        """Follow append-only successor links; never infer order from timestamps."""
        visited: set[str] = set()
        candidate_id = successor_publication_id
        while candidate_id not in visited:
            if candidate_id == publication_id:
                return True
            visited.add(candidate_id)
            if not self._registry.has_lifecycle(candidate_id):
                return False
            current = self._registry.get_current(candidate_id)
            if current.status is not PublicationLifecycleStatus.SUPERSEDED:
                return False
            candidate_id = current.successor_publication_id
        return True

    @staticmethod
    def _validate_identifiers(*values: str) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise InvalidPublicationLifecycleRecordError(
                "Lifecycle and publication identities must be non-empty strings."
            )

    @staticmethod
    def _validate_reason(reason: str) -> None:
        if not isinstance(reason, str) or not reason.strip():
            raise InvalidPublicationLifecycleTransitionError(
                "A terminal lifecycle transition requires a non-empty reason."
            )

    @staticmethod
    def _validate_timestamp(transitioned_at: datetime) -> None:
        if (
            not isinstance(transitioned_at, datetime)
            or transitioned_at.tzinfo is None
            or transitioned_at.tzinfo != timezone.utc
        ):
            raise InvalidPublicationLifecycleRecordError(
                "Transition timestamp must be an explicit UTC datetime."
            )

    @staticmethod
    def _validate_monotonic_timestamp(current: datetime, previous: datetime) -> None:
        if current < previous:
            raise InvalidPublicationLifecycleTransitionError(
                "Transition timestamp cannot be earlier than the current record."
            )


class StrategyEvaluationPublicationLifecycleService(
    _PublicationLifecycleService[PublishedStrategyEvaluationLifecycleRecord]
):
    """Manage lifecycle state of published strategy evaluations only."""

    _record_type = PublishedStrategyEvaluationLifecycleRecord

    def __init__(
        self,
        publication_access: StrategyEvaluationPublicationAccess,
        registry: PublishedStrategyEvaluationLifecycleRegistry,
    ) -> None:
        super().__init__(publication_access, registry)


class StrategyEvaluationComparisonPublicationLifecycleService(
    _PublicationLifecycleService[PublishedStrategyEvaluationComparisonLifecycleRecord]
):
    """Manage lifecycle state of published strategy comparisons only."""

    _record_type = PublishedStrategyEvaluationComparisonLifecycleRecord

    def __init__(
        self,
        publication_access: StrategyEvaluationComparisonPublicationAccess,
        registry: PublishedStrategyEvaluationComparisonLifecycleRegistry,
    ) -> None:
        super().__init__(publication_access, registry)
