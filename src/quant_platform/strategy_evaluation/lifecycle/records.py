"""Immutable, append-only records for published evidence lifecycle state."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidPublicationLifecycleRecordError,
)


class PublicationLifecycleStatus(StrEnum):
    """The complete lifecycle state set authorized for this MVP."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class _LifecycleRecordValidation:
    """Shared invariant validation; this is not a persisted domain type."""

    __slots__ = ()

    lifecycle_id: str
    publication_id: str
    status: PublicationLifecycleStatus
    previous_lifecycle_id: str | None
    successor_publication_id: str | None
    transitioned_at: datetime
    reason: str | None

    def __post_init__(self) -> None:
        self._identifier(self.lifecycle_id, "Lifecycle identity")
        self._identifier(self.publication_id, "Publication identity")
        if not isinstance(self.status, PublicationLifecycleStatus):
            raise InvalidPublicationLifecycleRecordError(
                "Lifecycle status must be a PublicationLifecycleStatus."
            )
        if not isinstance(self.transitioned_at, datetime):
            raise InvalidPublicationLifecycleRecordError(
                "Transition timestamp must be a datetime."
            )
        if (
            self.transitioned_at.tzinfo is None
            or self.transitioned_at.utcoffset() != timezone.utc.utcoffset(None)
            or self.transitioned_at.tzinfo != timezone.utc
        ):
            raise InvalidPublicationLifecycleRecordError(
                "Transition timestamp must be normalized to UTC."
            )
        if self.status is PublicationLifecycleStatus.ACTIVE:
            if any(
                value is not None
                for value in (
                    self.previous_lifecycle_id,
                    self.successor_publication_id,
                    self.reason,
                )
            ):
                raise InvalidPublicationLifecycleRecordError(
                    "An active initial record cannot have transition fields."
                )
            return
        self._identifier(self.previous_lifecycle_id, "Previous lifecycle identity")
        self._identifier(self.reason, "Transition reason")
        if self.status is PublicationLifecycleStatus.SUPERSEDED:
            self._identifier(self.successor_publication_id, "Successor publication identity")
        elif self.successor_publication_id is not None:
            raise InvalidPublicationLifecycleRecordError(
                "A withdrawn record cannot name a successor publication."
            )

    @staticmethod
    def _identifier(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InvalidPublicationLifecycleRecordError(
                f"{label} must be a non-empty string."
            )


@dataclass(frozen=True, slots=True)
class PublishedStrategyEvaluationLifecycleRecord(_LifecycleRecordValidation):
    """One immutable lifecycle event for a published strategy evaluation."""

    lifecycle_id: str
    publication_id: str
    status: PublicationLifecycleStatus
    previous_lifecycle_id: str | None
    successor_publication_id: str | None
    transitioned_at: datetime
    reason: str | None


@dataclass(frozen=True, slots=True)
class PublishedStrategyEvaluationComparisonLifecycleRecord(_LifecycleRecordValidation):
    """One immutable lifecycle event for a published strategy comparison."""

    lifecycle_id: str
    publication_id: str
    status: PublicationLifecycleStatus
    previous_lifecycle_id: str | None
    successor_publication_id: str | None
    transitioned_at: datetime
    reason: str | None
