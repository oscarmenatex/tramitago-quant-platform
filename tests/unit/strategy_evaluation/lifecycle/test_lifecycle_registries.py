"""LR-001..LR-010 evidence for both append-only lifecycle registries."""

import pytest

from quant_platform.strategy_evaluation import (
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    PublishedStrategyEvaluationLifecycleRegistry,
)
from quant_platform.strategy_evaluation.domain.exceptions import (
    DuplicatePublicationLifecycleIdError,
    InvalidPublicationLifecycleRecordError,
    PublicationLifecycleNotFoundError,
)

from .conftest import comparison_record, evaluation_record


class FailingMapping(dict):
    def __setitem__(self, key, value):
        raise RuntimeError("history index failed")


@pytest.mark.parametrize(
    ("registry_type", "factory"),
    [(PublishedStrategyEvaluationLifecycleRegistry, evaluation_record),
     (PublishedStrategyEvaluationComparisonLifecycleRegistry, comparison_record)],
)
def test_lrr_001_to_008_registry_reads_order_identity_and_duplicates(registry_type, factory):
    registry = registry_type()
    first = factory()
    second = factory(lifecycle_id="lifecycle-B", publication_id=first.publication_id)
    assert registry.append(first) is first and registry.append(second) is second
    assert registry.get(first.lifecycle_id) is first
    assert registry.exists(first.lifecycle_id) and not registry.exists("missing")
    assert registry.has_lifecycle(first.publication_id) and not registry.has_lifecycle("missing")
    assert registry.history(first.publication_id) == (first, second)
    assert registry.get_current(first.publication_id) is second
    assert registry.list() == (first, second) and isinstance(registry.list(), tuple)
    with pytest.raises(DuplicatePublicationLifecycleIdError):
        registry.append(first)
    with pytest.raises(PublicationLifecycleNotFoundError):
        registry.get("missing")
    with pytest.raises(PublicationLifecycleNotFoundError):
        registry.history("missing")
    with pytest.raises(InvalidPublicationLifecycleRecordError):
        registry.append(object())


@pytest.mark.parametrize(
    ("registry_type", "factory"),
    [(PublishedStrategyEvaluationLifecycleRegistry, evaluation_record),
     (PublishedStrategyEvaluationComparisonLifecycleRegistry, comparison_record)],
)
def test_lrr_009_to_010_rolls_back_and_preserves_original_cause(registry_type, factory):
    registry = registry_type()
    registry._by_publication_id = FailingMapping()
    value = factory()
    with pytest.raises(RuntimeError, match="history index failed") as raised:
        registry.append(value)
    assert raised.value.__cause__ is None
    assert not registry.exists(value.lifecycle_id)
    assert not registry.has_lifecycle(value.publication_id)
    assert registry.list() == ()
