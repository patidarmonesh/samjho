"""
test_reasoning.py — Validation logic tests. No API key required.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from models import ReasoningResult, is_label_compatible_with_skill
from reasoning import parse_and_validate, describe_result_state


class TestLabelCompatibility:
    def test_denominator_confusion_ok_for_compare(self):
        assert is_label_compatible_with_skill("denominator_size_confusion", "compare")

    def test_denominator_confusion_rejected_for_add(self):
        assert not is_label_compatible_with_skill("denominator_size_confusion", "add")

    def test_adds_num_denom_ok_for_add(self):
        assert is_label_compatible_with_skill("adds_numerators_and_denominators", "add")

    def test_adds_num_denom_rejected_for_compare(self):
        assert not is_label_compatible_with_skill("adds_numerators_and_denominators", "compare")

    def test_sound_reasoning_ok_for_both(self):
        assert is_label_compatible_with_skill("sound_reasoning", "compare")
        assert is_label_compatible_with_skill("sound_reasoning", "add")


class TestParseAndValidate:
    def _make_json(self, label, evidence="", explanation="test"):
        return json.dumps({"label": label, "evidence_quote": evidence, "explanation": explanation})

    def test_valid_insufficient_evidence(self):
        raw = self._make_json("insufficient_evidence")
        result = parse_and_validate(raw, "compare", "I guessed.")
        assert result.label == "insufficient_evidence"

    def test_unknown_label_rejected(self):
        raw = json.dumps({"label": "made_up_label", "evidence_quote": "", "explanation": "test"})
        with pytest.raises(Exception):
            parse_and_validate(raw, "compare", "some explanation")

    def test_extra_field_rejected(self):
        raw = json.dumps({
            "label": "insufficient_evidence",
            "evidence_quote": "",
            "explanation": "test",
            "confidence": 0.9,
        })
        with pytest.raises(Exception):
            parse_and_validate(raw, "compare", "some explanation")

    def test_fabricated_evidence_quote_downgraded(self):
        student_expl = "8 is bigger so 1/8 is bigger"
        # Model invents a quote not in student explanation
        raw = self._make_json(
            "denominator_size_confusion",
            evidence="FABRICATED QUOTE NOT IN STUDENT TEXT",
        )
        result = parse_and_validate(raw, "compare", student_expl)
        assert result.label == "insufficient_evidence"

    def test_valid_evidence_quote_accepted(self):
        student_expl = "8 is bigger so 1/8 is bigger"
        raw = self._make_json(
            "denominator_size_confusion",
            evidence="8 is bigger so 1/8 is bigger",
        )
        result = parse_and_validate(raw, "compare", student_expl)
        assert result.label == "denominator_size_confusion"

    def test_compare_label_rejected_for_add_skill(self):
        student_expl = "I added top and bottom"
        raw = self._make_json(
            "denominator_size_confusion",
            evidence="I added top and bottom",
        )
        result = parse_and_validate(raw, "add", student_expl)
        # Should be reclassified
        assert result.label != "denominator_size_confusion"

    def test_sound_reasoning_wrong_answer_does_not_mean_success(self):
        # sound_reasoning + wrong answer → state is "wrong_sound", not success
        state = describe_result_state(is_correct=False, label="sound_reasoning")
        assert state == "wrong_sound"

    def test_correct_answer_with_misconception_not_success(self):
        state = describe_result_state(is_correct=True, label="denominator_size_confusion")
        assert state == "correct_misconception"

    def test_malformed_json_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_and_validate("NOT JSON AT ALL {{{{", "compare", "test explanation")

    def test_empty_content_raises_value_error(self):
        with pytest.raises((ValueError, Exception)):
            parse_and_validate("", "compare", "test explanation")

    def test_markdown_fenced_json_stripped(self):
        raw = "```json\n" + json.dumps({
            "label": "insufficient_evidence",
            "evidence_quote": "",
            "explanation": "ok",
        }) + "\n```"
        result = parse_and_validate(raw, "compare", "test")
        assert result.label == "insufficient_evidence"


class TestDescribeResultState:
    def test_correct_and_sound(self):
        assert describe_result_state(True, "sound_reasoning") == "correct_sound"

    def test_correct_and_misconception(self):
        assert describe_result_state(True, "denominator_size_confusion") == "correct_misconception"

    def test_wrong_and_misconception(self):
        assert describe_result_state(False, "adds_numerators_and_denominators") == "wrong_misconception"

    def test_wrong_and_sound(self):
        assert describe_result_state(False, "sound_reasoning") == "wrong_sound"

    def test_insufficient_evidence(self):
        assert describe_result_state(True, "insufficient_evidence") == "clarify_needed"

    def test_other_reasoning(self):
        assert describe_result_state(False, "other_reasoning") == "other"
