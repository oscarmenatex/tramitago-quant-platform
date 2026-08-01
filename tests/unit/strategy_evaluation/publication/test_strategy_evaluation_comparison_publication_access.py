import pytest

from quant_platform.strategy_evaluation import (
    StrategyEvaluationComparisonPublicationAccess,
)
from quant_platform.strategy_evaluation.domain import (
    PublishedStrategyEvaluationComparisonNotFoundError,
)

from .conftest import published_comparison


class RegistrySpy:
    def __init__(self):
        self.value, self.calls = published_comparison(), []

    def get(self, value):
        self.calls.append(("get", value))
        return self.value

    def resolve(self, value):
        self.calls.append(("resolve", value))
        return self.value

    def exists(self, value):
        self.calls.append(("exists", value))
        return True

    def is_published(self, value):
        self.calls.append(("is_published", value))
        return True

    def list(self):
        self.calls.append(("list",))
        return (self.value,)


def test_comparison_access_delegates_each_read_operation_exactly():
    registry = RegistrySpy()
    access = StrategyEvaluationComparisonPublicationAccess(registry)
    assert access.get("p") is registry.value and access.resolve("c") is registry.value
    assert (
        access.exists("p")
        and access.is_published("c")
        and access.list() == (registry.value,)
    )
    assert registry.calls == [
        ("get", "p"),
        ("resolve", "c"),
        ("exists", "p"),
        ("is_published", "c"),
        ("list",),
    ]


def test_comparison_access_propagates_get_and_resolve_not_found():
    class NotFoundRegistry(RegistrySpy):
        def get(self, value):
            raise PublishedStrategyEvaluationComparisonNotFoundError(value)

        def resolve(self, value):
            raise PublishedStrategyEvaluationComparisonNotFoundError(value)

    access = StrategyEvaluationComparisonPublicationAccess(NotFoundRegistry())
    with pytest.raises(PublishedStrategyEvaluationComparisonNotFoundError):
        access.get("missing")
    with pytest.raises(PublishedStrategyEvaluationComparisonNotFoundError):
        access.resolve("missing")


def test_comparison_access_is_read_only():
    assert not hasattr(StrategyEvaluationComparisonPublicationAccess, "register")
