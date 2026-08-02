"""RR-T-001..RR-T-008 evidence for ResolutionResult."""

import pytest

from quant_platform.strategy_evaluation import ResolutionResult
from quant_platform.strategy_evaluation.domain.exceptions import InvalidResolutionResultError

from .conftest import published_comparison, published_evaluation


@pytest.mark.parametrize("publication", [published_evaluation(), published_comparison()])
def test_rr_t_001_to_006_supports_one_immutable_public_projection(publication):
    result = ResolutionResult(publication)
    assert result.publication is publication and result.publication_id == publication.publication_id
    assert result == ResolutionResult(publication)
    assert hash(result) == hash(ResolutionResult(publication))
    with pytest.raises(AttributeError):
        result.publication = publication


def test_rr_t_007_to_008_rejects_invalid_or_non_single_result():
    with pytest.raises(InvalidResolutionResultError):
        ResolutionResult(object())
    assert set(ResolutionResult.__dataclass_fields__) == {"publication"}
