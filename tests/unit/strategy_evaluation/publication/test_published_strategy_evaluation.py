from dataclasses import fields

import pytest

from quant_platform.strategy_evaluation import (
    PublishedStrategyEvaluation,
)
from quant_platform.strategy_evaluation.domain import (
    InvalidPublishedStrategyEvaluationError,
)

from .conftest import evaluation


def create(**changes):
    source = evaluation()
    values = dict(
        publication_id="publication",
        evaluation_id=source.id,
        strategy_id=source.strategy.id,
        knowledge_id=source.knowledge_id,
        knowledge_version=source.knowledge_version,
        context=source.context,
        criteria=source.strategy.criteria,
        result={"value": [1]},
    )
    values.update(changes)
    return PublishedStrategyEvaluation(**values)


def test_pe_001_valid_construction():
    assert create().evaluation_id == "evaluation"


def test_pe_002_invalid_publication_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(publication_id=" ")


def test_pe_003_invalid_evaluation_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(evaluation_id=" ")


def test_pe_004_invalid_strategy_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(strategy_id=" ")


def test_pe_005_invalid_knowledge_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(knowledge_id=" ")


def test_pe_006_invalid_knowledge_version():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(knowledge_version=" ")


def test_pe_007_invalid_context():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(context=object())


def test_pe_008_invalid_criteria():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(criteria=object())


def test_pe_009_empty_result():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(result={})


def test_pe_010_invalid_result_key():
    with pytest.raises(InvalidPublishedStrategyEvaluationError):
        create(result={" ": 1})


def test_pe_011_defensive_copy():
    source = {"value": [1]}
    value = create(result=source)
    source["value"].append(2)
    assert value.result["value"] == (1,)


def test_pe_012_recursive_immutability():
    value = create(result={"value": {"nested": [1]}})
    with pytest.raises(TypeError):
        value.result["value"]["new"] = 1


def test_pe_013_value_equality_and_authorized_fields():
    assert create() == create()
    assert {field.name for field in fields(PublishedStrategyEvaluation)} == {
        "publication_id",
        "evaluation_id",
        "strategy_id",
        "knowledge_id",
        "knowledge_version",
        "context",
        "criteria",
        "result",
    }
