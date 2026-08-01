"""LS-001..LS-015 and A-001..A-009 evidence for both lifecycle Services."""

from datetime import timedelta

import pytest

from quant_platform.strategy_evaluation import (
    PublicationLifecycleStatus,
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    PublishedStrategyEvaluationLifecycleRegistry,
    StrategyEvaluationComparisonPublicationLifecycleService,
    StrategyEvaluationPublicationLifecycleService,
)
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

from .conftest import INITIAL_TIME


class PublicationAccessSpy:
    def __init__(self, publication_ids=("A", "B", "C"), error=None):
        self.publication_ids, self.error, self.get_calls = set(publication_ids), error, 0

    def get(self, publication_id):
        self.get_calls += 1
        if self.error is not None:
            raise self.error
        if publication_id not in self.publication_ids:
            raise KeyError(publication_id)
        return object()

    def exists(self, publication_id):
        return publication_id in self.publication_ids


@pytest.fixture(params=[
    (StrategyEvaluationPublicationLifecycleService, PublishedStrategyEvaluationLifecycleRegistry),
    (StrategyEvaluationComparisonPublicationLifecycleService, PublishedStrategyEvaluationComparisonLifecycleRegistry),
])
def subject(request):
    service_type, registry_type = request.param
    registry = registry_type()
    return service_type(PublicationAccessSpy(), registry), registry


def _register_active(service, publication_id, lifecycle_id):
    return service.register_initial(
        lifecycle_id=lifecycle_id,
        publication_id=publication_id,
        transitioned_at=INITIAL_TIME,
    )


def test_lss_001_registers_active_once_and_returns_registry_instance(subject):
    service, registry = subject
    result = _register_active(service, "A", "active-A")
    assert result is registry.get("active-A")
    assert result.status is PublicationLifecycleStatus.ACTIVE
    assert result.previous_lifecycle_id is result.successor_publication_id is result.reason is None
    assert registry.list() == (result,)


@pytest.mark.parametrize("kwargs", [
    {"lifecycle_id": " ", "publication_id": "A", "transitioned_at": INITIAL_TIME},
    {"lifecycle_id": "active-A", "publication_id": " ", "transitioned_at": INITIAL_TIME},
    {"lifecycle_id": "active-A", "publication_id": "A", "transitioned_at": INITIAL_TIME.replace(tzinfo=None)},
])
def test_lss_002_invalid_initial_request_is_atomic(subject, kwargs):
    service, registry = subject
    with pytest.raises(InvalidPublicationLifecycleRecordError):
        service.register_initial(**kwargs)
    assert registry.list() == ()


def test_lss_003_duplicate_identity_and_second_initial_are_atomic(subject):
    service, registry = subject
    _register_active(service, "A", "active-A")
    with pytest.raises(DuplicatePublicationLifecycleIdError):
        service.register_initial(lifecycle_id="active-A", publication_id="B", transitioned_at=INITIAL_TIME)
    with pytest.raises(PublicationLifecycleAlreadyRegisteredError):
        service.register_initial(lifecycle_id="again-A", publication_id="A", transitioned_at=INITIAL_TIME)
    assert len(registry.list()) == 1


def test_lss_004_preserves_origin_not_found_and_does_not_append(subject):
    service, registry = subject
    error = KeyError("A")
    service._publication_access.error = error
    with pytest.raises(KeyError) as raised:
        _register_active(service, "A", "active-A")
    assert raised.value is error and registry.list() == ()


def test_lss_005_supersedes_active_origin_once_with_traceability(subject):
    service, registry = subject
    prior = _register_active(service, "A", "active-A")
    _register_active(service, "B", "active-B")
    result = service.supersede(
        lifecycle_id="superseded-A", publication_id="A", successor_publication_id="B",
        transitioned_at=INITIAL_TIME + timedelta(seconds=1), reason="replaced",
    )
    assert result is registry.get("superseded-A")
    assert (result.status, result.previous_lifecycle_id, result.successor_publication_id, result.reason) == (
        PublicationLifecycleStatus.SUPERSEDED, prior.lifecycle_id, "B", "replaced")
    assert len(registry.history("A")) == 2


def test_lss_006_withdraws_active_origin_once_with_traceability(subject):
    service, registry = subject
    prior = _register_active(service, "A", "active-A")
    result = service.withdraw(
        lifecycle_id="withdrawn-A", publication_id="A",
        transitioned_at=INITIAL_TIME + timedelta(seconds=1), reason="withdrawn",
    )
    assert (result.status, result.previous_lifecycle_id, result.successor_publication_id) == (
        PublicationLifecycleStatus.WITHDRAWN, prior.lifecycle_id, None)
    assert len(registry.history("A")) == 2


@pytest.mark.parametrize("operation", ["supersede", "withdraw"])
def test_lss_007_terminal_states_reject_every_further_transition(subject, operation):
    service, registry = subject
    _register_active(service, "A", "active-A")
    _register_active(service, "B", "active-B")
    service.withdraw(lifecycle_id="withdrawn-A", publication_id="A", transitioned_at=INITIAL_TIME, reason="withdrawn")
    with pytest.raises(PublicationAlreadyWithdrawnError):
        if operation == "supersede":
            service.supersede(lifecycle_id="again", publication_id="A", successor_publication_id="B", transitioned_at=INITIAL_TIME, reason="no")
        else:
            service.withdraw(lifecycle_id="again", publication_id="A", transitioned_at=INITIAL_TIME, reason="no")
    assert len(registry.history("A")) == 2


def test_lss_008_superseded_origin_is_terminal(subject):
    service, registry = subject
    _register_active(service, "A", "active-A")
    _register_active(service, "B", "active-B")
    service.supersede(lifecycle_id="superseded-A", publication_id="A", successor_publication_id="B", transitioned_at=INITIAL_TIME, reason="replaced")
    with pytest.raises(PublicationAlreadySupersededError):
        service.withdraw(lifecycle_id="again", publication_id="A", transitioned_at=INITIAL_TIME, reason="no")
    assert len(registry.history("A")) == 2


@pytest.mark.parametrize("operation", ["withdraw", "supersede"])
def test_lss_009_missing_origin_lifecycle_is_atomic(subject, operation):
    service, registry = subject
    with pytest.raises(PublicationLifecycleNotFoundError):
        if operation == "withdraw":
            service.withdraw(lifecycle_id="x", publication_id="A", transitioned_at=INITIAL_TIME, reason="reason")
        else:
            service.supersede(lifecycle_id="x", publication_id="A", successor_publication_id="B", transitioned_at=INITIAL_TIME, reason="reason")
    assert registry.list() == ()


def test_lss_010_rejects_each_successor_precondition_without_append(subject):
    service, registry = subject
    _register_active(service, "A", "active-A")
    before = registry.list()
    with pytest.raises(PublicationSuccessorNotFoundError):
        service.supersede(lifecycle_id="x", publication_id="A", successor_publication_id="missing", transitioned_at=INITIAL_TIME, reason="reason")
    with pytest.raises(PublicationLifecycleCycleError):
        service.supersede(lifecycle_id="self", publication_id="A", successor_publication_id="A", transitioned_at=INITIAL_TIME, reason="reason")
    with pytest.raises(PublicationSuccessorLifecycleNotFoundError):
        service.supersede(lifecycle_id="no-lifecycle", publication_id="A", successor_publication_id="B", transitioned_at=INITIAL_TIME, reason="reason")
    _register_active(service, "B", "active-B")
    service.withdraw(lifecycle_id="withdrawn-B", publication_id="B", transitioned_at=INITIAL_TIME, reason="withdrawn")
    with pytest.raises(PublicationSuccessorNotActiveError):
        service.supersede(lifecycle_id="not-active", publication_id="A", successor_publication_id="B", transitioned_at=INITIAL_TIME, reason="reason")
    assert registry.history("A") == before


def test_lss_011_detects_direct_and_indirect_successor_cycles(subject):
    service, registry = subject
    initial_a = _register_active(service, "A", "active-A")
    initial_b = _register_active(service, "B", "active-B")
    initial_c = _register_active(service, "C", "active-C")
    record_type = type(initial_a)
    registry.append(
        record_type(
            "superseded-A", "A", PublicationLifecycleStatus.SUPERSEDED,
            initial_a.lifecycle_id, "B", INITIAL_TIME, "replaced",
        )
    )
    registry.append(
        record_type(
            "superseded-B", "B", PublicationLifecycleStatus.SUPERSEDED,
            initial_b.lifecycle_id, "A", INITIAL_TIME, "replaced",
        )
    )
    assert service._would_create_cycle("A", "B")
    registry.append(
        record_type(
            "superseded-C", "C", PublicationLifecycleStatus.SUPERSEDED,
            initial_c.lifecycle_id, "A", INITIAL_TIME, "replaced",
        )
    )
    assert service._would_create_cycle("C", "A")


@pytest.mark.parametrize("method, kwargs", [
    ("supersede", {"successor_publication_id": "B", "reason": " "}),
    ("withdraw", {"reason": " "}),
])
def test_lss_012_invalid_reason_and_regressive_time_are_atomic(subject, method, kwargs):
    service, registry = subject
    _register_active(service, "A", "active-A")
    _register_active(service, "B", "active-B")
    base = {"lifecycle_id": "bad", "publication_id": "A", "transitioned_at": INITIAL_TIME, **kwargs}
    with pytest.raises(InvalidPublicationLifecycleTransitionError):
        getattr(service, method)(**base)
    base["reason"] = "valid"
    base["transitioned_at"] = INITIAL_TIME - timedelta(seconds=1)
    with pytest.raises(InvalidPublicationLifecycleTransitionError):
        getattr(service, method)(**base)
    assert len(registry.history("A")) == 1
