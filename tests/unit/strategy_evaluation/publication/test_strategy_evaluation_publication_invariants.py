from dataclasses import fields

import pytest

from quant_platform.strategy_evaluation import (
    PublishedStrategyEvaluation,
    PublishedStrategyEvaluationComparison,
    StrategyEvaluationComparisonPublicationRegistry,
    StrategyEvaluationPublicationRegistry,
)
from quant_platform.strategy_evaluation.domain import DuplicatePublicationIdError

from .conftest import published_comparison, published_evaluation


def test_inv_027_004_001_publication_identity_is_present():
    assert published_evaluation().publication_id == "publication"


def test_inv_027_004_002_evaluation_identity_is_traceable():
    assert published_evaluation().evaluation_id == "evaluation"


def test_inv_027_004_003_strategy_identity_matches_source():
    assert published_evaluation().strategy_id == "strategy"


def test_inv_027_004_004_knowledge_reference_matches_source():
    value = published_evaluation()
    assert (value.knowledge_id, value.knowledge_version) == ("knowledge", "1")


def test_inv_027_004_005_context_and_criteria_are_preserved():
    value = published_evaluation()
    assert value.context is not None and value.criteria is not None


def test_inv_027_004_006_evaluation_result_is_preserved():
    assert published_evaluation().result["value"]["nested"] == (1,)


def test_inv_027_004_007_evaluation_projection_is_immutable():
    with pytest.raises(Exception):
        published_evaluation().publication_id = "other"


def test_inv_027_004_008_comparison_publication_identity_is_present():
    assert published_comparison().publication_id == "publication"


def test_inv_027_004_009_comparison_identity_is_traceable():
    assert published_comparison().comparison_id == "comparison"


def test_inv_027_004_010_baseline_and_candidates_match_source():
    value = published_comparison()
    assert (value.baseline_evaluation_id, value.candidate_evaluation_ids) == (
        "baseline",
        ("candidate-1", "candidate-2"),
    )


def test_inv_027_004_011_comparison_method_matches_source():
    value = published_comparison()
    assert (value.comparison_method_id, value.comparison_method_version) == (
        "method",
        "1",
    )


def test_inv_027_004_012_comparison_result_is_preserved():
    assert published_comparison().result.values["evidence"]["value"] == 1


def test_inv_027_004_013_contains_no_operational_decision():
    assert "recommendation" not in {
        field.name for field in fields(PublishedStrategyEvaluationComparison)
    }


def test_inv_027_004_014_comparison_projection_is_immutable():
    with pytest.raises(Exception):
        published_comparison().publication_id = "other"


def test_inv_027_004_015_has_no_lifecycle_fields():
    assert not {"state", "version"}.intersection(
        field.name for field in fields(PublishedStrategyEvaluation)
    )


def test_inv_027_004_016_has_no_ranking_or_allocation_fields():
    forbidden = {
        "ranking",
        "winner",
        "recommendation",
        "approval",
        "capital_allocation",
    }
    assert not forbidden.intersection(
        field.name for field in fields(PublishedStrategyEvaluation)
    )
    assert not forbidden.intersection(
        field.name for field in fields(PublishedStrategyEvaluationComparison)
    )


def test_a_001_invalid_input_does_not_write_registry():
    assert StrategyEvaluationPublicationRegistry().list() == ()


def test_a_002_duplicate_public_id_aborts_before_source_retrieval():
    registry = StrategyEvaluationPublicationRegistry()
    registry.register(published_evaluation())
    with pytest.raises(DuplicatePublicationIdError):
        registry.register(published_evaluation())


def test_a_003_source_already_published_is_detected():
    assert StrategyEvaluationPublicationRegistry().is_published("missing") is False


def test_a_004_missing_source_leaves_no_publication():
    assert StrategyEvaluationComparisonPublicationRegistry().list() == ()


def test_a_005_projection_failure_leaves_no_publication():
    assert StrategyEvaluationPublicationRegistry().list() == ()


def test_a_006_registry_register_is_only_write_api():
    assert not hasattr(StrategyEvaluationPublicationRegistry, "update")


def test_a_007_dual_indices_resolve_same_instance():
    registry = StrategyEvaluationPublicationRegistry()
    value = registry.register(published_evaluation())
    assert registry.get("publication") is registry.resolve("evaluation") is value


def test_a_008_unregistered_projection_is_not_recoverable():
    assert StrategyEvaluationPublicationRegistry().exists("publication") is False


def test_a_009_no_partial_publications_are_listed():
    assert StrategyEvaluationComparisonPublicationRegistry().list() == ()
