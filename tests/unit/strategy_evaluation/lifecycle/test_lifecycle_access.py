"""LA-001..LA-005 evidence for both read-only lifecycle Access boundaries."""

import pytest

from quant_platform.strategy_evaluation import (
    PublishedStrategyEvaluationComparisonLifecycleAccess,
    PublishedStrategyEvaluationLifecycleAccess,
)
from quant_platform.strategy_evaluation.domain.exceptions import PublicationLifecycleNotFoundError

from .conftest import comparison_record, evaluation_record


class RegistrySpy:
    def __init__(self, value):
        self.value, self.calls = value, []

    def get(self, value):
        self.calls.append(("get", value))
        return self.value

    def exists(self, value):
        self.calls.append(("exists", value))
        return True

    def has_lifecycle(self, value):
        self.calls.append(("has_lifecycle", value))
        return True

    def get_current(self, value):
        self.calls.append(("get_current", value))
        return self.value

    def history(self, value):
        self.calls.append(("history", value))
        return (self.value,)

    def list(self):
        self.calls.append(("list",))
        return (self.value,)


@pytest.mark.parametrize(
    ("access_type", "factory"),
    [(PublishedStrategyEvaluationLifecycleAccess, evaluation_record),
     (PublishedStrategyEvaluationComparisonLifecycleAccess, comparison_record)],
)
def test_lra_001_to_004_delegates_every_read_and_is_read_only(access_type, factory):
    registry = RegistrySpy(factory())
    access = access_type(registry)
    assert access.get("id") is registry.value
    assert access.exists("id") and access.has_lifecycle("publication")
    assert access.get_current("publication") is registry.value
    assert access.history("publication") == (registry.value,)
    assert access.list() == (registry.value,)
    assert registry.calls == [("get", "id"), ("exists", "id"),
                              ("has_lifecycle", "publication"),
                              ("get_current", "publication"),
                              ("history", "publication"), ("list",)]
    assert not hasattr(access, "append") and not hasattr(access, "register")


@pytest.mark.parametrize(
    ("access_type", "factory"),
    [(PublishedStrategyEvaluationLifecycleAccess, evaluation_record),
     (PublishedStrategyEvaluationComparisonLifecycleAccess, comparison_record)],
)
def test_lra_005_propagates_not_found_unchanged(access_type, factory):
    class NotFoundRegistry(RegistrySpy):
        def get(self, value):
            raise PublicationLifecycleNotFoundError(value)

        def history(self, value):
            raise PublicationLifecycleNotFoundError(value)

    access = access_type(NotFoundRegistry(factory()))
    with pytest.raises(PublicationLifecycleNotFoundError):
        access.get("missing")
    with pytest.raises(PublicationLifecycleNotFoundError):
        access.history("missing")
