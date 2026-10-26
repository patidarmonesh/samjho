"""
models.py — Strict Pydantic schema for reasoning classification results.
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


ALLOWED_LABELS = Literal[
    "denominator_size_confusion",
    "adds_numerators_and_denominators",
    "sound_reasoning",
    "insufficient_evidence",
    "other_reasoning",
]

# Labels that are only valid for comparison-skill questions
COMPARE_ONLY_LABELS = {"denominator_size_confusion"}
# Labels that are only valid for addition-skill questions
ADD_ONLY_LABELS = {"adds_numerators_and_denominators"}


class ReasoningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: ALLOWED_LABELS
    evidence_quote: str = Field(max_length=500)
    explanation: str = Field(max_length=700)


def is_label_compatible_with_skill(label: str, skill: str) -> bool:
    """Return False if the label cannot apply to the given skill."""
    if label in COMPARE_ONLY_LABELS and skill != "compare":
        return False
    if label in ADD_ONLY_LABELS and skill != "add":
        return False
    return True
