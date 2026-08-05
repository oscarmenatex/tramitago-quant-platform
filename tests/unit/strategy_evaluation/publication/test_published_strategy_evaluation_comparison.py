from dataclasses import fields

import pytest

from quant_platform.strategy_evaluation import (
    PublishedStrategyEvaluationComparison,
)
from quant_platform.strategy_evaluation.domain import (
    InvalidPublishedStrategyEvaluationComparisonError,
)

from .conftest import comparison


def create(**changes):
    source = comparison()
    values = dict(
        publication_id="publication",
        comparison_id=source.id,
        baseline_evaluation_id=source.baseline_evaluation_id,
        candidate_evaluation_ids=source.candidate_evaluation_ids,
        comparison_method_id=source.comparison_method_id,
        comparison_method_version=source.comparison_method_version,
        result=source.result,
    )
    values.update(changes)
    return PublishedStrategyEvaluationComparison(**values)


def test_pc_001_valid_construction():
    assert create().comparison_id == "comparison"


def test_pc_002_invalid_publication_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(publication_id=" ")


def test_pc_003_invalid_comparison_id():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(comparison_id=" ")


def test_pc_004_invalid_baseline():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(baseline_evaluation_id=" ")


def test_pc_005_missing_candidates():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(candidate_evaluation_ids=())


def test_pc_006_invalid_candidate():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(candidate_evaluation_ids=(" ",))


def test_pc_007_baseline_is_candidate():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(candidate_evaluation_ids=("baseline",))


def test_pc_008_duplicate_candidate():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(candidate_evaluation_ids=("a", "a"))


def test_pc_009_invalid_method():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(comparison_method_id=" ")


def test_pc_010_invalid_version():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(comparison_method_version=" ")


def test_pc_011_invalid_result():
    with pytest.raises(InvalidPublishedStrategyEvaluationComparisonError):
        create(result=object())


def test_pc_012_candidate_order_is_preserved():
    assert create().candidate_evaluation_ids == ("candidate-1", "candidate-2")


def test_pc_013_immutable_and_authorized_fields():
    value = create()
    with pytest.raises(Exception):
        value.comparison_id = "other"
    assert {field.name for field in fields(PublishedStrategyEvaluationComparison)} == {
        "publication_id",
        "comparison_id",
        "baseline_evaluation_id",
        "candidate_evaluation_ids",
        "comparison_method_id",
        "comparison_method_version",
        "result",
    }
