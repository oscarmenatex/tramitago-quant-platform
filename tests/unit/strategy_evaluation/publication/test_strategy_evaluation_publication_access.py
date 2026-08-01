import ast
import inspect

import pytest

from quant_platform.strategy_evaluation import StrategyEvaluationPublicationAccess
from quant_platform.strategy_evaluation.domain import (
    PublishedStrategyEvaluationNotFoundError,
)

from .conftest import published_evaluation


class RegistrySpy:
    def __init__(self):
        self.value, self.calls = published_evaluation(), []

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


def test_access_delegates_each_read_operation_exactly():
    registry = RegistrySpy()
    access = StrategyEvaluationPublicationAccess(registry)
    assert access.get("p") is registry.value and access.resolve("e") is registry.value
    assert (
        access.exists("p")
        and access.is_published("e")
        and access.list() == (registry.value,)
    )
    assert registry.calls == [
        ("get", "p"),
        ("resolve", "e"),
        ("exists", "p"),
        ("is_published", "e"),
        ("list",),
    ]


def test_access_propagates_get_and_resolve_not_found():
    class NotFoundRegistry(RegistrySpy):
        def get(self, value):
            raise PublishedStrategyEvaluationNotFoundError(value)

        def resolve(self, value):
            raise PublishedStrategyEvaluationNotFoundError(value)

    access = StrategyEvaluationPublicationAccess(NotFoundRegistry())
    with pytest.raises(PublishedStrategyEvaluationNotFoundError):
        access.get("missing")
    with pytest.raises(PublishedStrategyEvaluationNotFoundError):
        access.resolve("missing")


def test_access_is_read_only_and_has_no_forbidden_imports():
    assert not hasattr(StrategyEvaluationPublicationAccess, "register")
    source_file = inspect.getsourcefile(StrategyEvaluationPublicationAccess)
    assert source_file is not None
    tree = ast.parse(open(source_file).read())
    imports = [
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert not any(
        "application" in module or ".registry.strategy_evaluation_access" in module
        for module in imports
    )
