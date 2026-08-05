"""INV-T-001..INV-T-010 evidence for Resolution invariants."""

import pytest

from quant_platform.strategy_evaluation import ResolutionContext, StrategyEvaluationPublicationResolutionService

from .conftest import active_comparison, active_evaluation


@pytest.mark.parametrize(
    ("register", "context", "publication_index", "lifecycle_index"),
    [
        (active_evaluation, ResolutionContext.for_evaluation, 4, 6),
        (active_comparison, ResolutionContext.for_comparison, 5, 7),
    ],
)
def test_inv_t_001_to_010_resolution_has_no_state_mutation_or_partial_result(
    boundaries, register, context, publication_index, lifecycle_index
):
    publication = register(boundaries[publication_index], boundaries[lifecycle_index])
    subject = StrategyEvaluationPublicationResolutionService(*boundaries[:4])
    before = tuple(access.list() for access in boundaries[:4])
    result = subject.resolve(context(publication.evaluation_id if publication_index == 4 else publication.comparison_id))
    assert result.publication == publication
    assert tuple(access.list() for access in boundaries[:4]) == before
