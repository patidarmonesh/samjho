"""
test_checks.py — Deterministic oracle tests. No API key required.
"""
import pytest
from fractions import Fraction
from checks import compare_pairs, add_pairs, fraction, fraction_equals


class TestCompare:
    def test_16_gt_18(self):
        assert compare_pairs((1, 6), (1, 8)) == "left"

    def test_13_gt_14(self):
        assert compare_pairs((1, 3), (1, 4)) == "left"

    def test_25_gt_27(self):
        assert compare_pairs((2, 5), (2, 7)) == "left"

    def test_equal(self):
        assert compare_pairs((1, 2), (2, 4)) == "equal"

    def test_right_larger(self):
        assert compare_pairs((1, 8), (1, 6)) == "right"


class TestAdd:
    def test_half_plus_third(self):
        result = add_pairs((1, 2), (1, 3))
        assert result == Fraction(5, 6)

    def test_quarter_plus_half(self):
        result = add_pairs((1, 4), (1, 2))
        assert result == Fraction(3, 4)

    def test_third_plus_sixth(self):
        result = add_pairs((1, 3), (1, 6))
        assert result == Fraction(1, 2)


class TestFraction:
    def test_positive_denominator_ok(self):
        f = fraction(1, 6)
        assert f == Fraction(1, 6)

    def test_zero_denominator_rejected(self):
        with pytest.raises(ValueError):
            fraction(1, 0)

    def test_negative_denominator_rejected(self):
        with pytest.raises(ValueError):
            fraction(1, -3)

    def test_fraction_equals(self):
        f = Fraction(5, 6)
        assert fraction_equals(f, 5, 6)
        assert not fraction_equals(f, 2, 5)
