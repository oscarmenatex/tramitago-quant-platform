from types import SimpleNamespace

import pytest

from quant_platform.strategy_evaluation import (
    StrategyEvaluationComparisonPublicationService,
)
from quant_platform.strategy_evaluation.domain import (
    DuplicatePublicationIdError,
    InvalidPublicationRequestError,
    PublicationProjectionError,
    StrategyEvaluationComparisonAlreadyPublishedError,
)

from .conftest import comparison


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
        (
            self.exists_value,
            self.published_value,
            self.returned,
            self.register_call_count,
            self.values,
        ) = exists, published, returned, 0, []

    def exists(self, identity):
        return self.exists_value

    def is_published(self, identity):
        return self.published_value

    def register(self, value):
        self.register_call_count += 1
        self.values.append(value)
        return self.returned if self.returned is not None else value


def service(source=None, registry=None, error=None):
    registry = registry or RegistrySpy()
    access = SourceAccessSpy(source or comparison(), error)
    return (
        StrategyEvaluationComparisonPublicationService(registry, access),
        registry,
        access,
    )


def test_cs_001_validates_both_identifiers():
    target, _, _ = service()
    for publication_id, comparison_id in (("", "c"), ("p", "")):
        with pytest.raises(InvalidPublicationRequestError):
            target.publish(publication_id=publication_id, comparison_id=comparison_id)


def test_cs_002_duplicate_public_id_precedes_source_read():
    target, registry, access = service(registry=RegistrySpy(exists=True))
    with pytest.raises(DuplicatePublicationIdError):
        target.publish(publication_id="p", comparison_id="c")
    assert access.get_call_count == registry.register_call_count == 0


def test_cs_003_republication_precedes_source_read():
    target, registry, access = service(registry=RegistrySpy(published=True))
    with pytest.raises(StrategyEvaluationComparisonAlreadyPublishedError):
        target.publish(publication_id="p", comparison_id="c")
    assert access.get_call_count == registry.register_call_count == 0


def test_cs_004_recovers_source_once_through_access():
    target, _, access = service()
    target.publish(publication_id="p", comparison_id="comparison")
    assert access.get_call_count == 1


def test_cs_005_preserves_baseline_candidates_method_and_version():
    source = comparison()
    target, _, _ = service(source)
    published = target.publish(publication_id="p", comparison_id="comparison")
    assert (
        published.baseline_evaluation_id,
        published.candidate_evaluation_ids,
        published.comparison_method_id,
        published.comparison_method_version,
    ) == (
        source.baseline_evaluation_id,
        source.candidate_evaluation_ids,
        source.comparison_method_id,
        source.comparison_method_version,
    )


def test_cs_006_preserves_candidate_order():
    assert service()[0].publish(
        publication_id="p", comparison_id="comparison"
    ).candidate_evaluation_ids == ("candidate-1", "candidate-2")


def test_cs_007_reuses_comparison_result():
    source = comparison()
    assert (
        service(source)[0]
        .publish(publication_id="p", comparison_id="comparison")
        .result
        is source.result
    )


def test_cs_008_constructs_public_projection():
    assert (
        service()[0]
        .publish(publication_id="p", comparison_id="comparison")
        .publication_id
        == "p"
    )


def test_cs_009_registers_exactly_once():
    target, registry, _ = service()
    target.publish(publication_id="p", comparison_id="comparison")
    assert registry.register_call_count == 1


def test_cs_010_returns_registry_instance():
    returned = object()
    target, _, _ = service(registry=RegistrySpy(returned=returned))
    assert target.publish(publication_id="p", comparison_id="comparison") is returned


def test_ce_001_invalid_request_is_atomic():
    target, registry, access = service()
    with pytest.raises(InvalidPublicationRequestError):
        target.publish(publication_id="", comparison_id="c")
    assert access.get_call_count == registry.register_call_count == 0


def test_ce_002_duplicate_public_id_is_atomic():
    test_cs_002_duplicate_public_id_precedes_source_read()


def test_ce_003_republication_is_atomic():
    test_cs_003_republication_precedes_source_read()


def test_ce_004_source_not_found_is_preserved():
    error = KeyError("missing")
    target, registry, _ = service(error=error)
    with pytest.raises(KeyError) as raised:
        target.publish(publication_id="p", comparison_id="c")
    assert raised.value is error and registry.register_call_count == 0


def test_ce_005_invalid_projection_does_not_register():
    bad = SimpleNamespace(
        id="c",
        baseline_evaluation_id="b",
        candidate_evaluation_ids=("x",),
        comparison_method_id="m",
        comparison_method_version="1",
        result=object(),
    )
    target, registry, _ = service(bad)
    with pytest.raises(PublicationProjectionError):
        target.publish(publication_id="p", comparison_id="c")
    assert registry.register_call_count == 0


def test_ce_006_projection_exception_is_chained():
    bad = SimpleNamespace(
        id="c",
        baseline_evaluation_id="b",
        candidate_evaluation_ids=("x",),
        comparison_method_id="m",
        comparison_method_version="1",
        result=object(),
    )
    target, _, _ = service(bad)
    with pytest.raises(PublicationProjectionError) as raised:
        target.publish(publication_id="p", comparison_id="c")
    assert raised.value.__cause__ is not None


def test_ce_007_every_pre_registration_failure_leaves_registry_empty():
    target, registry, _ = service(error=KeyError("missing"))
    with pytest.raises(KeyError):
        target.publish(publication_id="p", comparison_id="c")
    assert registry.values == []


def test_ce_008_does_not_revalidate_comparison_process_rules():
    service()[0].publish(publication_id="p", comparison_id="comparison")
