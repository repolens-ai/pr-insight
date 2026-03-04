import pytest
from pr_insight.algo.utils import ModelType, ReasoningEffort, Range


class TestModelType:
    def test_model_type_values(self):
        assert ModelType.REGULAR.value == "regular"
        assert ModelType.WEAK.value == "weak"
        assert ModelType.REASONING.value == "reasoning"


class TestReasoningEffort:
    def test_reasoning_effort_values(self):
        assert ReasoningEffort.XHIGH.value == "xhigh"
        assert ReasoningEffort.HIGH.value == "high"
        assert ReasoningEffort.MEDIUM.value == "medium"
        assert ReasoningEffort.LOW.value == "low"
        assert ReasoningEffort.MINIMAL.value == "minimal"
        assert ReasoningEffort.NONE.value == "none"

    def test_reasoning_effort_from_string(self):
        assert ReasoningEffort("xhigh") == ReasoningEffort.XHIGH
        assert ReasoningEffort("high") == ReasoningEffort.HIGH


class TestRange:
    def test_range_creation(self):
        r = Range(line_start=0, line_end=10)
        assert r.line_start == 0
        assert r.line_end == 10
        assert r.column_start == -1
        assert r.column_end == -1

    def test_range_with_columns(self):
        r = Range(line_start=5, line_end=15, column_start=10, column_end=20)
        assert r.line_start == 5
        assert r.line_end == 15
        assert r.column_start == 10
        assert r.column_end == 20

    def test_range_model_validation(self):
        r = Range.model_validate({"line_start": 1, "line_end": 5})
        assert r.line_start == 1
        assert r.line_end == 5

    def test_range_json_serialization(self):
        r = Range(line_start=0, line_end=10)
        json_str = r.model_dump_json()
        assert "line_start" in json_str
        assert "line_end" in json_str
