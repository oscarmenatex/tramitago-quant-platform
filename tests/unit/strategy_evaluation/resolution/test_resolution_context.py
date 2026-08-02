"""RC-T-001..RC-T-008 evidence for ResolutionContext."""

import pytest

from quant_platform.strategy_evaluation import PublicationResolutionKind, ResolutionContext
from quant_platform.strategy_evaluation.domain.exceptions import InvalidResolutionContextError


def test_rc_t_001_to_005_constructs_immutable_value_with_identity_and_hash():
    context = ResolutionContext.for_evaluation("evaluation-A")
    assert context == ResolutionContext("evaluation-A", PublicationResolutionKind.EVALUATION)
    assert hash(context) == hash(ResolutionContext.for_evaluation("evaluation-A"))
    with pytest.raises(AttributeError):
        context.source_id = "other"


@pytest.mark.parametrize("args", [("", PublicationResolutionKind.EVALUATION), ("source", "evaluation")])
def test_rc_t_006_to_008_rejects_missing_and_invalid_or_forbidden_shape(args):
    with pytest.raises(InvalidResolutionContextError):
        ResolutionContext(*args)
    assert set(ResolutionContext.__dataclass_fields__) == {"source_id", "publication_kind"}
