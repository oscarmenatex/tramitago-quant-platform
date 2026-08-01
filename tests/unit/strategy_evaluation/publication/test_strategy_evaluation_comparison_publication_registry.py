import pytest

from quant_platform.strategy_evaluation import (
    StrategyEvaluationComparisonPublicationRegistry,
)
from quant_platform.strategy_evaluation.domain import (
    DuplicatePublicationIdError,
    PublishedStrategyEvaluationComparisonNotFoundError,
    StrategyEvaluationComparisonAlreadyPublishedError,
)

from .conftest import published_comparison


class FailingMapping(dict):
    def __setitem__(self, key, value):
        raise RuntimeError("second index failed")


def test_cr_001_registers_valid_publication():
    assert StrategyEvaluationComparisonPublicationRegistry().register(
        published_comparison()
    )


def test_cr_002_returns_same_instance():
    value = published_comparison()
    assert StrategyEvaluationComparisonPublicationRegistry().register(value) is value


def test_cr_003_rejects_duplicate_publication_id():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    registry.register(published_comparison())
    with pytest.raises(DuplicatePublicationIdError):
        registry.register(published_comparison())


def test_cr_004_rejects_already_published_source():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    registry.register(published_comparison())
    with pytest.raises(StrategyEvaluationComparisonAlreadyPublishedError):
        registry.register(published_comparison("other", "comparison"))


def test_cr_005_get_by_publication_id():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    value = registry.register(published_comparison())
    assert registry.get("publication") is value


def test_cr_006_get_not_found():
    with pytest.raises(PublishedStrategyEvaluationComparisonNotFoundError):
        StrategyEvaluationComparisonPublicationRegistry().get("missing")


def test_cr_007_resolve_by_source_id():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    value = registry.register(published_comparison())
    assert registry.resolve("comparison") is value


def test_cr_008_resolve_not_found():
    with pytest.raises(PublishedStrategyEvaluationComparisonNotFoundError):
        StrategyEvaluationComparisonPublicationRegistry().resolve("missing")


def test_cr_009_exists_true_and_false():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    registry.register(published_comparison())
    assert registry.exists("publication") and not registry.exists("missing")


def test_cr_010_is_published_true_and_false():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    registry.register(published_comparison())
    assert registry.is_published("comparison") and not registry.is_published("missing")


def test_cr_011_list_is_tuple():
    assert isinstance(StrategyEvaluationComparisonPublicationRegistry().list(), tuple)


def test_cr_012_list_preserves_publication_order():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    first = registry.register(published_comparison("one", "one"))
    second = registry.register(published_comparison("two", "two"))
    assert registry.list() == (first, second)


def test_cr_013_indices_remain_coherent_after_second_write_failure():
    registry = StrategyEvaluationComparisonPublicationRegistry()
    registry._by_comparison_id = FailingMapping()
    with pytest.raises(RuntimeError):
        registry.register(published_comparison())
    assert (
        not registry.exists("publication")
        and not registry.is_published("comparison")
        and registry.list() == ()
    )
    registry._by_comparison_id = {}
    assert registry.register(published_comparison()) is registry.get("publication")
    assert not hasattr(registry, "update") and not hasattr(registry, "delete")
