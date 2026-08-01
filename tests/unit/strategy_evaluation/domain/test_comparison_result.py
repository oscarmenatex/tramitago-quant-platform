import pytest

from quant_platform.strategy_evaluation.domain import (
    ComparisonResult,
    InvalidComparisonResultError,
)


def test_comparison_result_is_immutable_and_equal_by_value() -> None:
    values = {"evidence": {"same": True}, "delta": 0}
    result = ComparisonResult(values)
    values["evidence"]["same"] = False

    assert result == ComparisonResult({"delta": 0, "evidence": {"same": True}})
    with pytest.raises(TypeError):
        result.values["evidence"]["same"] = False


def test_comparison_result_freezes_each_nested_container_and_preserves_input_copy():
    values = {
        "mapping": {"x": 1},
        "list": [1],
        "tuple": (1,),
        "set": {1},
        "frozen": frozenset({1}),
    }
    result = ComparisonResult(values)
    values["mapping"]["x"] = 2
    values["list"].append(2)
    values["set"].add(2)
    assert result.values["mapping"]["x"] == 1
    assert result.values["list"] == (1,)
    assert result.values["tuple"] == (1,)
    assert result.values["set"] == frozenset({1})
    assert result.values["frozen"] == frozenset({1})


def test_comparison_result_equality_is_independent_of_mapping_order():
    assert ComparisonResult({"a": 1, "b": 2}) == ComparisonResult({"b": 2, "a": 1})


@pytest.mark.parametrize(
    "values", [{}, {1: "invalid"}, {"": "invalid"}, {"   ": "invalid"}]
)
def test_comparison_result_rejects_invalid_values(values: dict[object, object]) -> None:
    with pytest.raises(InvalidComparisonResultError):
        ComparisonResult(values)
