"""
test_state.py — Content/curriculum integrity tests. No API key required.
"""
import pytest
from fractions import Fraction

from content import QUESTIONS, get_diagnostic_question
from checks import compare_pairs, add_pairs, fraction_equals


class TestCurriculumOracle:
    """Every question's declared correct option must agree with the Fraction oracle."""

    def test_compare_01_oracle(self):
        q = QUESTIONS["compare_01"]
        oracle = compare_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        assert correct_opt.value == oracle  # "left"

    def test_compare_02_oracle(self):
        q = QUESTIONS["compare_02"]
        oracle = compare_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        assert correct_opt.value == oracle

    def test_compare_03_oracle(self):
        q = QUESTIONS["compare_03"]
        oracle = compare_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        assert correct_opt.value == oracle

    def test_add_01_oracle(self):
        q = QUESTIONS["add_01"]
        s = add_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        n, d = correct_opt.value.split("/")
        assert fraction_equals(s, int(n), int(d))

    def test_add_02_oracle(self):
        q = QUESTIONS["add_02"]
        s = add_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        n, d = correct_opt.value.split("/")
        assert fraction_equals(s, int(n), int(d))

    def test_add_03_oracle(self):
        q = QUESTIONS["add_03"]
        s = add_pairs(*q.operand_pairs)
        correct_opt = next(o for o in q.options if o.id == q.correct_option_id)
        n, d = correct_opt.value.split("/")
        assert fraction_equals(s, int(n), int(d))


class TestQuestionStructure:
    def test_all_questions_have_required_fields(self):
        for qid, q in QUESTIONS.items():
            assert q.id == qid
            assert q.skill in ("compare", "add")
            assert q.role in ("diagnostic", "transfer", "practice")
            assert len(q.options) >= 2
            assert q.correct_option_id in [o.id for o in q.options]
            assert len(q.operand_pairs) == 2
            assert q.lesson_en
            assert q.lesson_hi

    def test_diagnostic_questions_exist_for_each_skill(self):
        assert get_diagnostic_question("compare") is not None
        assert get_diagnostic_question("add") is not None

    def test_total_question_count(self):
        assert len(QUESTIONS) == 6
