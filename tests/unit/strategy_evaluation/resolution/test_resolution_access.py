"""Evidence that Resolution consumes public accesses without extending them."""

from quant_platform.strategy_evaluation import StrategyEvaluationPublicationResolutionService


def test_resolution_service_exposes_only_the_resolution_operation():
    assert [name for name in vars(StrategyEvaluationPublicationResolutionService) if not name.startswith("_")] == ["resolve"]
