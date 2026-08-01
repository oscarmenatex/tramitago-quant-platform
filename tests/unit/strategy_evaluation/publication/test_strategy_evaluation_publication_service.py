from types import SimpleNamespace

import pytest

from quant_platform.strategy_evaluation import StrategyEvaluationPublicationService
from quant_platform.strategy_evaluation.domain import (
    DuplicatePublicationIdError,
    InvalidPublicationRequestError,
    PublicationProjectionError,
    StrategyEvaluationAlreadyPublishedError,
)

from .conftest import evaluation


class SourceAccessSpy:
    def __init__(self, source=None, error=None):
        self.source, self.error, self.get_call_count = source, error, 0

    def get(self, identity):
        self.get_call_count += 1
        if self.error:
            raise self.error
        return self.source


class RegistrySpy:
    def __init__(self, *, exists=False, published=False, returned=None):
        self.exists_value, self.published_value, self.returned = (
            exists,
            published,
            returned,
        )
        self.register_call_count, self.values = 0, []

    def exists(self, identity):
        return self.exists_value

    def is_published(self, identity):
        return self.published_value

    def register(self, value):
        self.register_call_count += 1
        self.values.append(value)
        return self.returned if self.returned is not None else value


def test_es_001_validates_both_identifiers():
    for publication_id, evaluation_id in (("", "e"), ("p", "")):
        with pytest.raises(InvalidPublicationRequestError):
            StrategyEvaluationPublicationService(
                RegistrySpy(), SourceAccessSpy()
            ).publish(publication_id=publication_id, evaluation_id=evaluation_id)


def test_es_002_duplicate_public_id_precedes_source_read():
    access = SourceAccessSpy(evaluation())
    registry = RegistrySpy(exists=True)
    with pytest.raises(DuplicatePublicationIdError):
        StrategyEvaluationPublicationService(registry, access).publish(
            publication_id="p", evaluation_id="e"
        )
    assert access.get_call_count == registry.register_call_count == 0


def test_es_003_republication_precedes_source_read():
    access = SourceAccessSpy(evaluation())
    registry = RegistrySpy(published=True)
    with pytest.raises(StrategyEvaluationAlreadyPublishedError):
        StrategyEvaluationPublicationService(registry, access).publish(
            publication_id="p", evaluation_id="e"
        )
    assert access.get_call_count == registry.register_call_count == 0


def test_es_004_recovers_source_once_through_access():
    access = SourceAccessSpy(evaluation())
    registry = RegistrySpy()
    StrategyEvaluationPublicationService(registry, access).publish(
        publication_id="p", evaluation_id="evaluation"
    )
    assert access.get_call_count == 1


def test_es_005_preserves_all_canonical_fields():
    source = evaluation()
    registry = RegistrySpy()
    published = StrategyEvaluationPublicationService(
        registry, SourceAccessSpy(source)
    ).publish(publication_id="p", evaluation_id="evaluation")
    assert (
        published.evaluation_id,
        published.strategy_id,
        published.knowledge_id,
        published.knowledge_version,
        published.context,
    ) == (
        source.id,
        source.strategy.id,
        source.knowledge_id,
        source.knowledge_version,
        source.context,
    )


def test_es_006_criteria_comes_from_source_strategy():
    source = evaluation()
    published = StrategyEvaluationPublicationService(
        RegistrySpy(), SourceAccessSpy(source)
    ).publish(publication_id="p", evaluation_id="evaluation")
    assert published.criteria is source.strategy.criteria


def test_es_007_result_is_preserved_without_transformation():
    source = evaluation()
    published = StrategyEvaluationPublicationService(
        RegistrySpy(), SourceAccessSpy(source)
    ).publish(publication_id="p", evaluation_id="evaluation")
    assert published.result == source.result


def test_es_008_constructs_public_projection():
    assert (
        StrategyEvaluationPublicationService(
            RegistrySpy(), SourceAccessSpy(evaluation())
        )
        .publish(publication_id="p", evaluation_id="evaluation")
        .publication_id
        == "p"
    )


def test_es_009_registers_exactly_once():
    registry = RegistrySpy()
    StrategyEvaluationPublicationService(
        registry, SourceAccessSpy(evaluation())
    ).publish(publication_id="p", evaluation_id="evaluation")
    assert registry.register_call_count == 1


def test_es_010_returns_registry_instance():
    returned = object()
    registry = RegistrySpy(returned=returned)
    assert (
        StrategyEvaluationPublicationService(
            registry, SourceAccessSpy(evaluation())
        ).publish(publication_id="p", evaluation_id="evaluation")
        is returned
    )


def test_ee_001_invalid_request_is_atomic():
    access = SourceAccessSpy(evaluation())
    registry = RegistrySpy()
    with pytest.raises(InvalidPublicationRequestError):
        StrategyEvaluationPublicationService(registry, access).publish(
            publication_id="", evaluation_id="e"
        )
    assert access.get_call_count == registry.register_call_count == 0


def test_ee_002_duplicate_public_id_is_atomic():
    test_es_002_duplicate_public_id_precedes_source_read()


def test_ee_003_republication_is_atomic():
    test_es_003_republication_precedes_source_read()


def test_ee_004_source_not_found_is_preserved():
    error = KeyError("missing")
    registry = RegistrySpy()
    with pytest.raises(KeyError) as raised:
        StrategyEvaluationPublicationService(
            registry, SourceAccessSpy(error=error)
        ).publish(publication_id="p", evaluation_id="e")
    assert raised.value is error and registry.register_call_count == 0


def test_ee_005_invalid_projection_does_not_register():
    registry = RegistrySpy()
    bad = SimpleNamespace(
        id="e",
        strategy=SimpleNamespace(id="s", criteria=object()),
        knowledge_id="k",
        knowledge_version="1",
        context=object(),
        result={"x": 1},
    )
    with pytest.raises(PublicationProjectionError):
        StrategyEvaluationPublicationService(registry, SourceAccessSpy(bad)).publish(
            publication_id="p", evaluation_id="e"
        )
    assert registry.register_call_count == 0


def test_ee_006_projection_exception_is_chained():
    registry = RegistrySpy()
    bad = SimpleNamespace(
        id="e",
        strategy=SimpleNamespace(id="s", criteria=object()),
        knowledge_id="k",
        knowledge_version="1",
        context=object(),
        result={"x": 1},
    )
    with pytest.raises(PublicationProjectionError) as raised:
        StrategyEvaluationPublicationService(registry, SourceAccessSpy(bad)).publish(
            publication_id="p", evaluation_id="e"
        )
    assert raised.value.__cause__ is not None


def test_ee_007_every_pre_registration_failure_leaves_registry_empty():
    registry = RegistrySpy()
    access = SourceAccessSpy(error=KeyError("missing"))
    with pytest.raises(KeyError):
        StrategyEvaluationPublicationService(registry, access).publish(
            publication_id="p", evaluation_id="e"
        )
    assert registry.values == []


def test_ee_008_does_not_revalidate_evaluation_process_rules():
    source = evaluation()
    StrategyEvaluationPublicationService(
        RegistrySpy(), SourceAccessSpy(source)
    ).publish(publication_id="p", evaluation_id="evaluation")
