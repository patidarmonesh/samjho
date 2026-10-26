"""
content.py — Six hand-authored bilingual fraction questions with checked lessons.
All numeric data is trusted curriculum content; no student/model text is stored here.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional


@dataclass(frozen=True)
class QuestionOption:
    id: str          # stable key for session state
    label_en: str
    label_hi: str
    # For comparison questions: which side is selected ("left"/"right"/"equal")
    # For addition questions: numerator/denominator of the chosen answer
    value: str       # string encoding: "left"|"right"|"equal" or "N/D"


@dataclass(frozen=True)
class Question:
    id: str
    skill: str            # "compare" or "add"
    role: str             # "diagnostic" | "transfer" | "practice"
    prompt_en: str
    prompt_hi: str
    options: tuple        # tuple of QuestionOption
    correct_option_id: str
    # For visual: pairs of (numerator, denominator)
    operand_pairs: tuple  # e.g. ((1, 6), (1, 8)) for compare; same for add
    lesson_en: str
    lesson_hi: str
    followup_ids: tuple   # IDs of follow-up questions


QUESTIONS: dict[str, "Question"] = {}


def _reg(q: Question) -> Question:
    QUESTIONS[q.id] = q
    return q


# ── COMPARE skill ────────────────────────────────────────────────────────────

_reg(Question(
    id="compare_01",
    skill="compare",
    role="diagnostic",
    prompt_en="Which is larger: 1/6 or 1/8? Explain why.",
    prompt_hi="1/6 और 1/8 में कौन बड़ा है? कारण भी बताओ।",
    options=(
        QuestionOption("opt_16", "1/6", "1/6", "left"),
        QuestionOption("opt_18", "1/8", "1/8", "right"),
        QuestionOption("opt_eq", "They are equal", "दोनों बराबर हैं", "equal"),
    ),
    correct_option_id="opt_16",
    operand_pairs=((1, 6), (1, 8)),
    lesson_en=(
        "Imagine two rotis of the same size. Cut one into 6 equal pieces and the other "
        "into 8. One of the 6 pieces is larger than one of the 8 pieces. Therefore 1/6 "
        "is greater than 1/8. When the numerator is the same and positive, a larger "
        "positive denominator means smaller pieces — so the fraction is smaller."
    ),
    lesson_hi=(
        "दो बराबर आकार की रोटियाँ सोचो। एक को 6 बराबर टुकड़ों में और दूसरी को 8 बराबर "
        "टुकड़ों में बाँटो। 6 में से एक टुकड़ा, 8 में से एक टुकड़े से बड़ा होगा। इसलिए "
        "1/6, 1/8 से बड़ा है। जब ऊपर की धनात्मक संख्या समान हो, तो नीचे की बड़ी धनात्मक "
        "संख्या छोटे हिस्से बताती है — यानी वह भिन्न छोटी होती है।"
    ),
    followup_ids=("compare_02", "compare_03"),
))

_reg(Question(
    id="compare_02",
    skill="compare",
    role="transfer",
    prompt_en="Which is larger: 1/3 or 1/4? Explain why.",
    prompt_hi="1/3 और 1/4 में कौन बड़ा है? कारण भी बताओ।",
    options=(
        QuestionOption("opt_13", "1/3", "1/3", "left"),
        QuestionOption("opt_14", "1/4", "1/4", "right"),
        QuestionOption("opt_eq", "They are equal", "दोनों बराबर हैं", "equal"),
    ),
    correct_option_id="opt_13",
    operand_pairs=((1, 3), (1, 4)),
    lesson_en=(
        "Divide the same whole into 3 equal parts: each part is 1/3. Now divide the "
        "same whole into 4 equal parts: each part is 1/4. Fewer pieces from the same "
        "whole means each piece is bigger. So 1/3 > 1/4."
    ),
    lesson_hi=(
        "उसी पूरी चीज़ को 3 बराबर हिस्सों में बाँटो: हर हिस्सा 1/3 है। अब उसी पूरी चीज़ "
        "को 4 बराबर हिस्सों में बाँटो: हर हिस्सा 1/4 है। जितने कम टुकड़े, उतना बड़ा हर "
        "टुकड़ा। इसलिए 1/3 > 1/4।"
    ),
    followup_ids=("compare_03",),
))

_reg(Question(
    id="compare_03",
    skill="compare",
    role="practice",
    prompt_en="Which is larger: 2/5 or 2/7? Explain why.",
    prompt_hi="2/5 और 2/7 में कौन बड़ा है? कारण भी बताओ।",
    options=(
        QuestionOption("opt_25", "2/5", "2/5", "left"),
        QuestionOption("opt_27", "2/7", "2/7", "right"),
        QuestionOption("opt_eq", "They are equal", "दोनों बराबर हैं", "equal"),
    ),
    correct_option_id="opt_25",
    operand_pairs=((2, 5), (2, 7)),
    lesson_en=(
        "Both fractions take 2 pieces from the same whole. Dividing into 5 parts gives "
        "larger pieces than dividing into 7 parts. Two larger pieces (2/5) is therefore "
        "more than two smaller pieces (2/7). When the numerators are the same positive "
        "number, the fraction with the smaller denominator is larger."
    ),
    lesson_hi=(
        "दोनों भिन्न उसी पूरी चीज़ के 2 हिस्से लेती हैं। 5 भागों में बाँटने पर हर भाग "
        "बड़ा होता है, 7 भागों में बाँटने पर हर भाग छोटा। दो बड़े हिस्से (2/5) दो छोटे "
        "हिस्सों (2/7) से ज़्यादा हैं। जब ऊपर की संख्याएँ समान हों, तो कम नीचे वाली "
        "संख्या वाली भिन्न बड़ी होती है।"
    ),
    followup_ids=(),
))

# ── ADD skill ─────────────────────────────────────────────────────────────────

_reg(Question(
    id="add_01",
    skill="add",
    role="diagnostic",
    prompt_en="What is 1/2 + 1/3? Explain your method.",
    prompt_hi="1/2 + 1/3 कितना है? अपना तरीका बताओ।",
    options=(
        QuestionOption("opt_25", "2/5", "2/5", "2/5"),
        QuestionOption("opt_56", "5/6", "5/6", "5/6"),
        QuestionOption("opt_16", "1/6", "1/6", "1/6"),
    ),
    correct_option_id="opt_56",
    operand_pairs=((1, 2), (1, 3)),
    lesson_en=(
        "We can add pieces directly only when they have the same size. Rewrite 1/2 as "
        "3/6 and 1/3 as 2/6. Now 3/6 + 2/6 = 5/6. Adding the denominators would "
        "wrongly change the size of the pieces."
    ),
    lesson_hi=(
        "हिस्सों को सीधे जोड़ने के लिए उनका आकार बराबर होना चाहिए। 1/2 को 3/6 और 1/3 "
        "को 2/6 लिखो। अब 3/6 + 2/6 = 5/6। नीचे की संख्याओं को जोड़ने से हिस्सों का "
        "आकार गलत बदल जाएगा।"
    ),
    followup_ids=("add_02", "add_03"),
))

_reg(Question(
    id="add_02",
    skill="add",
    role="transfer",
    prompt_en="What is 1/4 + 1/2? Explain your method.",
    prompt_hi="1/4 + 1/2 कितना है? अपना तरीका बताओ।",
    options=(
        QuestionOption("opt_26", "2/6", "2/6", "2/6"),
        QuestionOption("opt_34", "3/4", "3/4", "3/4"),
        QuestionOption("opt_18", "1/8", "1/8", "1/8"),
    ),
    correct_option_id="opt_34",
    operand_pairs=((1, 4), (1, 2)),
    lesson_en=(
        "Convert to the same denominator. 1/2 = 2/4. Then 1/4 + 2/4 = 3/4. "
        "Always find a common denominator so the pieces are the same size before adding."
    ),
    lesson_hi=(
        "दोनों को एक ही हर वाली भिन्न बनाओ। 1/2 = 2/4। फिर 1/4 + 2/4 = 3/4। "
        "जोड़ने से पहले हमेशा समान हर ढूँढो ताकि हिस्सों का आकार बराबर हो।"
    ),
    followup_ids=("add_03",),
))

_reg(Question(
    id="add_03",
    skill="add",
    role="practice",
    prompt_en="What is 1/3 + 1/6? Explain your method.",
    prompt_hi="1/3 + 1/6 कितना है? अपना तरीका बताओ।",
    options=(
        QuestionOption("opt_29", "2/9", "2/9", "2/9"),
        QuestionOption("opt_12", "1/2", "1/2", "1/2"),
        QuestionOption("opt_118", "1/18", "1/18", "1/18"),
    ),
    correct_option_id="opt_12",
    operand_pairs=((1, 3), (1, 6)),
    lesson_en=(
        "Convert 1/3 to 2/6. Then 2/6 + 1/6 = 3/6 = 1/2. "
        "Once the denominators match, add the numerators and simplify."
    ),
    lesson_hi=(
        "1/3 को 2/6 बनाओ। फिर 2/6 + 1/6 = 3/6 = 1/2। "
        "जब हर एक हो जाएँ, तब ऊपर की संख्याएँ जोड़ो और सरल करो।"
    ),
    followup_ids=(),
))


def get_question(qid: str) -> Question:
    return QUESTIONS[qid]


def get_questions_for_skill(skill: str) -> list[Question]:
    return [q for q in QUESTIONS.values() if q.skill == skill]


def get_diagnostic_question(skill: str) -> Optional[Question]:
    for q in QUESTIONS.values():
        if q.skill == skill and q.role == "diagnostic":
            return q
    return None
