"""
checks.py — Deterministic fraction-based answer oracle using Python's Fraction.
Never uses eval() or LLM-generated arithmetic.
"""

from fractions import Fraction as _Fraction


def fraction(numerator: int, denominator: int) -> _Fraction:
    """Return a Fraction; reject non-positive denominators per curriculum rules."""
    if denominator <= 0:
        raise ValueError(
            f"This curriculum requires positive denominators; got {denominator}"
        )
    return _Fraction(numerator, denominator)


def compare_pairs(left: tuple[int, int], right: tuple[int, int]) -> str:
    """Return 'left', 'right', or 'equal' comparing two fractions."""
    a, b = fraction(*left), fraction(*right)
    if a > b:
        return "left"
    if a < b:
        return "right"
    return "equal"


def add_pairs(left: tuple[int, int], right: tuple[int, int]) -> _Fraction:
    """Return the exact sum of two fractions."""
    return fraction(*left) + fraction(*right)


def fraction_equals(f: _Fraction, numerator: int, denominator: int) -> bool:
    """Check whether a Fraction equals a given numerator/denominator pair."""
    return f == fraction(numerator, denominator)
