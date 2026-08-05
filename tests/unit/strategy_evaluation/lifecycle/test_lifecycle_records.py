"""LD-001..LD-010 contract evidence for both lifecycle record types."""

from dataclasses import FrozenInstanceError, fields
from datetime import datetime, timedelta, timezone

import pytest

from quant_platform.strategy_evaluation import PublicationLifecycleStatus
from quant_platform.strategy_evaluation.domain.exceptions import (
    InvalidPublicationLifecycleRecordError,
)

from .conftest import INITIAL_TIME, comparison_record, evaluation_record


@pytest.mark.parametrize("factory", [evaluation_record, comparison_record])
def test_lr_001_active_construction_is_immutable_and_value_equal(factory):
    value = factory()
    assert value == factory() and value.status is PublicationLifecycleStatus.ACTIVE
    with pytest.raises(FrozenInstanceError):
        value.lifecycle_id = "changed"


@pytest.mark.parametrize("factory", [evaluation_record, comparison_record])
def test_lr_002_terminal_construction_preserves_required_traceability(factory):
    superseded = factory(
        status=PublicationLifecycleStatus.SUPERSEDED,
        previous_lifecycle_id="previous",
        successor_publication_id="successor",
        transitioned_at=INITIAL_TIME + timedelta(seconds=1),
        reason="replaced",
    )
    withdrawn = factory(
        status=PublicationLifecycleStatus.WITHDRAWN,
        previous_lifecycle_id="previous",
        successor_publication_id=None,
        transitioned_at=INITIAL_TIME + timedelta(seconds=1),
        reason="withdrawn",
    )
    assert superseded.successor_publication_id == "successor"
    assert withdrawn.successor_publication_id is None


@pytest.mark.parametrize("factory", [evaluation_record, comparison_record])
@pytest.mark.parametrize(
    "changes",
    [
        {"lifecycle_id": " "},
        {"publication_id": " "},
        {"status": "active"},
        {"transitioned_at": datetime(2024, 1, 1)},
        {"transitioned_at": datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=1)))},
        {"status": PublicationLifecycleStatus.ACTIVE, "reason": "not initial"},
        {"status": PublicationLifecycleStatus.SUPERSEDED, "previous_lifecycle_id": " "},
        {"status": PublicationLifecycleStatus.SUPERSEDED, "successor_publication_id": " "},
        {"status": PublicationLifecycleStatus.SUPERSEDED, "reason": " "},
        {"status": PublicationLifecycleStatus.WITHDRAWN, "previous_lifecycle_id": " "},
        {"status": PublicationLifecycleStatus.WITHDRAWN, "successor_publication_id": "successor"},
        {"status": PublicationLifecycleStatus.WITHDRAWN, "reason": " "},
    ],
)
def test_lr_003_rejects_every_invalid_record_field(factory, changes):
    with pytest.raises(InvalidPublicationLifecycleRecordError):
        factory(**changes)


@pytest.mark.parametrize("factory", [evaluation_record, comparison_record])
def test_lr_004_exposes_only_the_normative_record_fields(factory):
    assert {field.name for field in fields(factory())} == {
        "lifecycle_id", "publication_id", "status", "previous_lifecycle_id",
        "successor_publication_id", "transitioned_at", "reason",
    }
