import pytest

from quant_platform.strategy_evaluation import StrategyEvaluationPublicationRegistry
from quant_platform.strategy_evaluation.domain import (
    DuplicatePublicationIdError,
    PublishedStrategyEvaluationNotFoundError,
    StrategyEvaluationAlreadyPublishedError,
)

from .conftest import published_evaluation


class FailingMapping(dict):
    def __setitem__(self, key, value):
        raise RuntimeError("second index failed")


def test_er_001_registers_valid_publication():
    assert StrategyEvaluationPublicationRegistry().register(published_evaluation())


def test_er_002_returns_same_instance():
    value = published_evaluation()
    assert StrategyEvaluationPublicationRegistry().register(value) is value


def test_er_003_rejects_duplicate_publication_id():
    registry = StrategyEvaluationPublicationRegistry()
    registry.register(published_evaluation())
    with pytest.raises(DuplicatePublicationIdError):
        registry.register(published_evaluation())


def test_er_004_rejects_already_published_source():
    registry = StrategyEvaluationPublicationRegistry()
    registry.register(published_evaluation())
    with pytest.raises(StrategyEvaluationAlreadyPublishedError):
        registry.register(published_evaluation("other", "evaluation"))


def test_er_005_get_by_publication_id():
    registry = StrategyEvaluationPublicationRegistry()
    value = registry.register(published_evaluation())
    assert registry.get("publication") is value


def test_er_006_get_not_found():
    with pytest.raises(PublishedStrategyEvaluationNotFoundError):
        StrategyEvaluationPublicationRegistry().get("missing")


def test_er_007_resolve_by_source_id():
    registry = StrategyEvaluationPublicationRegistry()
    value = registry.register(published_evaluation())
    assert registry.resolve("evaluation") is value


def test_er_008_resolve_not_found():
    with pytest.raises(PublishedStrategyEvaluationNotFoundError):
        StrategyEvaluationPublicationRegistry().resolve("missing")


def test_er_009_exists_true_and_false():
    registry = StrategyEvaluationPublicationRegistry()
    registry.register(published_evaluation())
    assert registry.exists("publication") and not registry.exists("missing")


def test_er_010_is_published_true_and_false():
    registry = StrategyEvaluationPublicationRegistry()
    registry.register(published_evaluation())
    assert registry.is_published("evaluation") and not registry.is_published("missing")


def test_er_011_list_is_tuple():
    assert isinstance(StrategyEvaluationPublicationRegistry().list(), tuple)


def test_er_012_list_preserves_publication_order():
    registry = StrategyEvaluationPublicationRegistry()
    first = registry.register(published_evaluation("one", "one"))
    second = registry.register(published_evaluation("two", "two"))
    assert registry.list() == (first, second)


def test_er_013_indices_remain_coherent_after_second_write_failure():
    registry = StrategyEvaluationPublicationRegistry()
    registry._by_evaluation_id = FailingMapping()
    with pytest.raises(RuntimeError):
        registry.register(published_evaluation())
    assert (
        not registry.exists("publication")
        and not registry.is_published("evaluation")
        and registry.list() == ()
    )
    registry._by_evaluation_id = {}
    assert registry.register(published_evaluation()) is registry.get("publication")
    assert not hasattr(registry, "update") and not hasattr(registry, "delete")
