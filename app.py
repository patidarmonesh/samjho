"""
app.py — Samjho: Explain your thinking. Understand your mistake.
Created by Monesh Patidar — Sole creator and developer, IIT Kanpur.
"""

import json

import streamlit as st

from checks import compare_pairs, add_pairs, fraction_equals
from content import QUESTIONS, get_diagnostic_question, get_question
from models import ReasoningResult
from reasoning import build_messages, parse_and_validate, select_lesson, describe_result_state
from sarvam_client import SarvamError, transcribe, classify_reasoning, synthesize_speech

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Samjho",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .samjho-title { font-size: 2.2rem; font-weight: 800; color: #1e2d40; margin-bottom: 0; }
  .samjho-sub   { font-size: 1rem; color: #4a6070; margin-top: 0; }
  .samjho-hi    { font-size: 0.95rem; color: #6a7f8a; font-style: italic; }
  .misconception-card {
      background: #fff8e1; border-left: 4px solid #f59e0b;
      padding: 1rem 1.2rem; border-radius: 6px; margin: 0.8rem 0;
  }
  .lesson-card {
      background: #e0f2f1; border-left: 4px solid #0d9488;
      padding: 1rem 1.2rem; border-radius: 6px; margin: 0.8rem 0;
  }
  .success-card {
      background: #e8f5e9; border-left: 4px solid #43a047;
      padding: 1rem 1.2rem; border-radius: 6px; margin: 0.8rem 0;
  }
  .info-card {
      background: #e3f2fd; border-left: 4px solid #1e88e5;
      padding: 1rem 1.2rem; border-radius: 6px; margin: 0.8rem 0;
  }
  .privacy-note { font-size: 0.78rem; color: #7a8a95; margin-top: 0.3rem; }
  .footer { text-align: center; font-size: 0.78rem; color: #9aabb5; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_api_key() -> str | None:
    try:
        key = st.secrets.get("SARVAM_API_KEY", "")
        return key if key and not key.startswith("your-") else None
    except Exception:
        return None


def init_state():
    defaults = {
        "language": "hi",
        "skill": "compare",
        "question_id": "compare_01",
        "attempt_id": 1,
        "phase": "answer",
        "confirmed_explanation": "",
        "analysis": None,
        "history": [],
        "last_request_fingerprint": None,
        "tts_bytes": None,
        "transcript_raw": "",
        "show_transfer": False,
        "transfer_question_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_question_state():
    """Clear per-question state when question or skill changes."""
    for key in [
        "confirmed_explanation", "analysis", "last_request_fingerprint",
        "tts_bytes", "transcript_raw", "show_transfer", "transfer_question_id",
        "phase",
    ]:
        st.session_state[key] = (
            "" if "explanation" in key or "transcript" in key or "fingerprint" in key
            else None if key in ("analysis", "tts_bytes", "transfer_question_id")
            else False if key in ("show_transfer",)
            else "answer"
        )
    st.session_state["attempt_id"] = st.session_state.get("attempt_id", 1) + 1


def compute_fingerprint() -> str:
    return json.dumps({
        "qid": st.session_state.question_id,
        "attempt": st.session_state.attempt_id,
        "lang": st.session_state.language,
        "expl": st.session_state.confirmed_explanation,
    }, ensure_ascii=False)


def is_answer_correct(question, selected_option_id: str) -> bool:
    """Use Python Fraction oracle — never LLM arithmetic."""
    if selected_option_id is None:
        return False
    opt_map = {o.id: o for o in question.options}
    if selected_option_id not in opt_map:
        return False
    selected_val = opt_map[selected_option_id].value

    if question.skill == "compare":
        left, right = question.operand_pairs
        oracle = compare_pairs(left, right)
        return selected_val == oracle

    # add skill
    left, right = question.operand_pairs
    correct_sum = add_pairs(left, right)
    # Parse the option value string "N/D"
    try:
        n_str, d_str = selected_val.split("/")
        return fraction_equals(correct_sum, int(n_str), int(d_str))
    except Exception:
        return False


def fraction_bar_svg(numerator: int, denominator: int, color: str = "#0d9488",
                     label: str = "") -> str:
    """Generate SVG fraction bar from trusted numeric curriculum data only."""
    cell_w = 30
    cell_h = 30
    total_w = cell_w * denominator + 2
    svg_parts = [
        f'<svg width="{total_w}" height="{cell_h + 20}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    ]
    for i in range(denominator):
        x = i * cell_w + 1
        fill = color if i < numerator else "#e0e0e0"
        svg_parts.append(
            f'<rect x="{x}" y="1" width="{cell_w - 2}" height="{cell_h - 2}" '
            f'fill="{fill}" stroke="#bbb" stroke-width="1" rx="2"/>'
        )
    if label:
        svg_parts.append(
            f'<text x="{total_w // 2}" y="{cell_h + 14}" '
            f'text-anchor="middle" font-size="12" fill="#333">{label}</text>'
        )
    svg_parts.append("</svg>")
    return "".join(svg_parts)


def render_fraction_visual(question):
    """Render fraction bars from trusted curriculum data."""
    lang = st.session_state.language
    st.markdown("#### 📊 " + ("भिन्न चित्र" if lang == "hi" else "Fraction Visual"))

    if question.skill == "compare":
        left, right = question.operand_pairs
        n1, d1 = left
        n2, d2 = right
        cols = st.columns(2)
        with cols[0]:
            st.markdown(
                fraction_bar_svg(n1, d1, "#0d9488", f"{n1}/{d1}"),
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(
                fraction_bar_svg(n2, d2, "#6b7280", f"{n2}/{d2}"),
                unsafe_allow_html=True,
            )
        st.caption(
            "हर बार एक ही पूरी चीज़ को बाँटा गया है।" if lang == "hi"
            else "Each bar represents the same whole."
        )

    elif question.skill == "add":
        left, right = question.operand_pairs
        n1, d1 = left
        n2, d2 = right
        from fractions import Fraction
        f1, f2 = Fraction(n1, d1), Fraction(n2, d2)
        f_sum = f1 + f2
        lcd = f_sum.denominator
        # Show equivalent common-denominator bars
        eq1_n = (lcd // d1) * n1
        eq2_n = (lcd // d2) * n2
        st.markdown(
            fraction_bar_svg(n1, d1, "#0d9488", f"{n1}/{d1}"),
            unsafe_allow_html=True,
        )
        st.markdown(
            fraction_bar_svg(n2, d2, "#6b7280", f"+ {n2}/{d2}"),
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown(
            fraction_bar_svg(eq1_n, lcd, "#0d9488", f"= {eq1_n}/{lcd}"),
            unsafe_allow_html=True,
        )
        st.markdown(
            fraction_bar_svg(eq2_n, lcd, "#6b7280", f"+ {eq2_n}/{lcd}"),
            unsafe_allow_html=True,
        )
        st.markdown(
            fraction_bar_svg(f_sum.numerator, f_sum.denominator, "#f59e0b",
                             f"= {f_sum.numerator}/{f_sum.denominator}"),
            unsafe_allow_html=True,
        )
        st.caption(
            "समान हर में बदलकर जोड़ा।" if lang == "hi"
            else "Converted to a common denominator before adding."
        )


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    api_key = get_api_key()
    lang = st.session_state.language

    with st.sidebar:
        st.markdown("## 🧮 Samjho")
        st.caption("Created by **Monesh Patidar** · IIT Kanpur")
        st.divider()

        # Language
        lang_choice = st.radio(
            "Language / भाषा",
            ["Hindi (हिंदी)", "English"],
            index=0 if lang == "hi" else 1,
            key="lang_radio",
        )
        new_lang = "hi" if lang_choice.startswith("Hindi") else "en"
        if new_lang != st.session_state.language:
            st.session_state.language = new_lang
            reset_question_state()
            st.rerun()

        # Skill
        skill_choice = st.selectbox(
            "Skill / विषय",
            options=["compare", "add"],
            format_func=lambda s: (
                ("भिन्न की तुलना" if lang == "hi" else "Compare Fractions")
                if s == "compare"
                else ("भिन्न जोड़" if lang == "hi" else "Add Fractions")
            ),
            index=["compare", "add"].index(st.session_state.skill),
            key="skill_select",
        )
        if skill_choice != st.session_state.skill:
            st.session_state.skill = skill_choice
            diag = get_diagnostic_question(skill_choice)
            st.session_state.question_id = diag.id if diag else list(QUESTIONS.keys())[0]
            reset_question_state()
            st.rerun()

        # Question picker
        skill_qs = [q for q in QUESTIONS.values() if q.skill == st.session_state.skill]
        q_labels = {
            q.id: f"[{q.role.upper()[0]}] {q.prompt_en[:35]}…"
            for q in skill_qs
        }
        chosen_qid = st.selectbox(
            "Question / प्रश्न",
            options=[q.id for q in skill_qs],
            format_func=lambda qid: q_labels[qid],
            index=[q.id for q in skill_qs].index(st.session_state.question_id),
            key="q_select",
        )
        if chosen_qid != st.session_state.question_id:
            st.session_state.question_id = chosen_qid
            reset_question_state()
            st.rerun()

        st.divider()

        # API status
        if api_key:
            st.success("✅ API configured")
        else:
            st.warning(
                "⚠️ API key not found.\n\n"
                "Add `SARVAM_API_KEY` to `.streamlit/secrets.toml`.\n\n"
                "The UI works in text mode without live AI."
            )

        # Reset
        if st.button("🔄 Reset session", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()
        with st.expander("ℹ️ Privacy & About"):
            st.markdown("""
**Privacy note:** Your explanation text and recordings are sent to Sarvam
for transcription and reasoning analysis. This prototype does not
intentionally save audio to disk. Avoid including personal details.
Provider processing is subject to Sarvam's privacy policy.

**Limitations:** Misconception labels are tentative, not diagnoses.
The app covers 2 fraction skills. No mastery tracking or account.

**Stack:** Streamlit · Sarvam AI · Python · Pydantic
""")


# ── Main UI ───────────────────────────────────────────────────────────────────

def main():
    init_state()
    render_sidebar()

    api_key = get_api_key()
    lang = st.session_state.language
    question = get_question(st.session_state.question_id)

    # Header
    st.markdown('<p class="samjho-title">🧮 Samjho</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="samjho-sub">Explain your thinking. Understand your mistake.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="samjho-hi">अपनी सोच बताओ। समझकर आगे बढ़ो।</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    # Question display
    role_badge = {"diagnostic": "🔍 पहचान", "transfer": "🔁 अभ्यास", "practice": "📝 और अभ्यास"}
    st.markdown(f"**{role_badge.get(question.role, question.role)}**")

    prompt = question.prompt_hi if lang == "hi" else question.prompt_en
    st.markdown(f"### {prompt}")

    # MCQ options — default unset (None)
    option_labels = [
        (o.id, o.label_hi if lang == "hi" else o.label_en)
        for o in question.options
    ]
    option_keys = [o.id for o in question.options]

    widget_key = f"mcq_{question.id}_{st.session_state.attempt_id}"
    selected_label = st.radio(
        "अपना उत्तर चुनो:" if lang == "hi" else "Select your answer:",
        options=[None] + option_keys,
        format_func=lambda oid: (
            ("— चुनें —" if lang == "hi" else "— select —") if oid is None
            else next(lbl for k, lbl in option_labels if k == oid)
        ),
        key=widget_key,
        horizontal=True,
    )

    st.divider()

    # ── Phase: answer → get explanation ───────────────────────────────────────
    st.markdown(
        "**अपनी सोच बताओ:**" if lang == "hi"
        else "**Explain your thinking:**"
    )

    # Voice input
    st.markdown(
        '<p class="privacy-note">🎤 '
        'आपकी रिकॉर्डिंग Sarvam को transcription के लिए भेजी जाती है। '
        'Samjho audio disk पर नहीं रखता। छोटी व्याख्या दें, व्यक्तिगत जानकारी न दें।'
        if lang == "hi" else
        '<p class="privacy-note">🎤 '
        'Your recording is sent to Sarvam for transcription. '
        'Samjho does not save audio to disk. Use a short explanation without personal details.'
        "</p>",
        unsafe_allow_html=True,
    )

    audio_key = f"audio_{question.id}_{st.session_state.attempt_id}"
    audio_data = st.audio_input(
        "Record your explanation (max 25 sec)" if lang == "en"
        else "अपनी व्याख्या रिकॉर्ड करें (अधिकतम 25 सेकंड)",
        key=audio_key,
    )

    if audio_data is not None:
        wav_bytes = audio_data.getvalue()
        if st.button(
            "📝 Transcribe recording" if lang == "en" else "📝 रिकॉर्डिंग transcribe करें",
            key=f"transcribe_btn_{question.id}_{st.session_state.attempt_id}",
        ):
            if not api_key:
                st.error(
                    "API key not configured. Type your explanation below instead."
                    if lang == "en"
                    else "API key नहीं मिली। नीचे text में लिखें।"
                )
            else:
                with st.spinner("Transcribing…"):
                    try:
                        transcript = transcribe(api_key, wav_bytes)
                        if transcript:
                            st.session_state.transcript_raw = transcript
                            st.session_state.phase = "transcript_review"
                            # clear old analysis
                            st.session_state.analysis = None
                            st.session_state.last_request_fingerprint = None
                            st.rerun()
                        else:
                            st.warning(
                                "Transcript is empty. Please re-record or type below."
                                if lang == "en"
                                else "Transcript खाली है। दोबारा रिकॉर्ड करें या नीचे टाइप करें।"
                            )
                    except SarvamError as exc:
                        st.error(f"Transcription error: {exc}")

    # Transcript review phase
    if st.session_state.phase == "transcript_review" and st.session_state.transcript_raw:
        st.info(
            "✏️ Check what I heard before continuing. Edit if needed, then click Analyze."
            if lang == "en"
            else "✏️ आगे बढ़ने से पहले जाँचें कि मैंने क्या सुना। ज़रूरत हो तो बदलें, फिर Analyze करें।"
        )
        edited = st.text_area(
            "Confirmed transcript:" if lang == "en" else "पुष्टि की गई transcript:",
            value=st.session_state.transcript_raw,
            key=f"transcript_edit_{question.id}_{st.session_state.attempt_id}",
            height=80,
        )
        if edited != st.session_state.confirmed_explanation:
            st.session_state.analysis = None
            st.session_state.last_request_fingerprint = None
        st.session_state.confirmed_explanation = edited

    # Text explanation (always available)
    text_key = f"text_expl_{question.id}_{st.session_state.attempt_id}"
    typed = st.text_area(
        "Type your explanation:" if lang == "en" else "अपनी व्याख्या टाइप करें:",
        value=(
            st.session_state.confirmed_explanation
            if st.session_state.phase != "transcript_review"
            else ""
        ),
        placeholder=(
            "e.g. 8 is bigger so 1/8 is bigger..."
            if lang == "en"
            else "जैसे: 8 बड़ा है इसलिए 1/8 बड़ा है..."
        ),
        key=text_key,
        height=80,
    )
    if st.session_state.phase != "transcript_review" and typed != st.session_state.confirmed_explanation:
        st.session_state.confirmed_explanation = typed
        # Invalidate old analysis on edit
        st.session_state.analysis = None
        st.session_state.last_request_fingerprint = None

    st.divider()

    # ── Analyze button ─────────────────────────────────────────────────────────
    can_analyze = (
        selected_label is not None
        and st.session_state.confirmed_explanation.strip()
    )

    analyze_btn = st.button(
        "🔍 Analyze my reasoning" if lang == "en" else "🔍 मेरी सोच जाँचें",
        disabled=not can_analyze,
        type="primary",
        key=f"analyze_{question.id}_{st.session_state.attempt_id}",
    )

    if not can_analyze and st.session_state.phase != "feedback":
        if selected_label is None:
            st.caption(
                "Please select an answer above." if lang == "en"
                else "पहले ऊपर एक उत्तर चुनें।"
            )
        elif not st.session_state.confirmed_explanation.strip():
            st.caption(
                "Please write or record your explanation." if lang == "en"
                else "कृपया अपनी व्याख्या लिखें या रिकॉर्ड करें।"
            )

    if analyze_btn and can_analyze:
        fingerprint = compute_fingerprint()
        if fingerprint == st.session_state.last_request_fingerprint and st.session_state.analysis:
            pass  # Reuse existing, don't re-call
        else:
            if not api_key:
                # Fixture mode — clearly labelled
                st.warning(
                    "⚠️ **DEMO / FIXTURE MODE** — API key not configured. "
                    "Showing a labelled placeholder, not a live AI result."
                    if lang == "en"
                    else
                    "⚠️ **DEMO / FIXTURE MODE** — API key नहीं मिली। "
                    "यह live AI नहीं है — placeholder दिखाया जा रहा है।"
                )
                st.session_state.analysis = ReasoningResult(
                    label="insufficient_evidence",
                    evidence_quote="",
                    explanation="[FIXTURE — no API key configured]",
                )
                st.session_state.last_request_fingerprint = fingerprint
            else:
                with st.spinner("Analyzing reasoning…" if lang == "en" else "सोच जाँची जा रही है…"):
                    messages = build_messages(question, st.session_state.confirmed_explanation)
                    try:
                        raw_content = classify_reasoning(api_key, messages)
                        try:
                            result = parse_and_validate(
                                raw_content,
                                question.skill,
                                st.session_state.confirmed_explanation,
                            )
                        except ValueError:
                            # One repair attempt
                            try:
                                repair_messages = messages + [
                                    {"role": "assistant", "content": raw_content},
                                    {
                                        "role": "user",
                                        "content": (
                                            "Your response was not valid JSON with the required keys "
                                            "(label, evidence_quote, explanation). "
                                            "Return only a JSON object with exactly those three keys."
                                        ),
                                    },
                                ]
                                raw_content2 = classify_reasoning(api_key, repair_messages)
                                result = parse_and_validate(
                                    raw_content2,
                                    question.skill,
                                    st.session_state.confirmed_explanation,
                                )
                            except (ValueError, SarvamError):
                                result = ReasoningResult(
                                    label="insufficient_evidence",
                                    evidence_quote="",
                                    explanation="Analysis unavailable. Please retry or type more detail.",
                                )

                        st.session_state.analysis = result
                        st.session_state.last_request_fingerprint = fingerprint
                        st.session_state.phase = "feedback"

                        # Log attempt
                        st.session_state.history.append({
                            "question_id": question.id,
                            "skill": question.skill,
                            "selected_option": selected_label,
                            "correct": is_answer_correct(question, selected_label),
                            "label": result.label,
                            "explanation_snippet": st.session_state.confirmed_explanation[:80],
                        })
                        st.rerun()

                    except SarvamError as exc:
                        st.error(f"API error: {exc}")

    # ── Feedback phase ─────────────────────────────────────────────────────────
    if st.session_state.analysis and st.session_state.phase == "feedback":
        result: ReasoningResult = st.session_state.analysis
        correct = is_answer_correct(question, selected_label)
        state = describe_result_state(correct, result.label)
        lesson_text = select_lesson(question, lang)

        st.divider()
        st.markdown("## " + ("परिणाम" if lang == "hi" else "Feedback"))

        # Answer correctness
        if correct:
            st.markdown(
                '<div class="success-card">✅ '
                + ("उत्तर सही है!" if lang == "hi" else "Correct answer!")
                + "</div>",
                unsafe_allow_html=True,
            )
        else:
            correct_opt = next(o for o in question.options if o.id == question.correct_option_id)
            correct_label = correct_opt.label_hi if lang == "hi" else correct_opt.label_en
            st.markdown(
                '<div class="misconception-card">❌ '
                + (f"उत्तर गलत है। सही उत्तर: **{correct_label}**" if lang == "hi"
                   else f"Incorrect. Correct answer: **{correct_label}**")
                + "</div>",
                unsafe_allow_html=True,
            )

        # Reasoning feedback
        if state == "correct_sound":
            st.markdown(
                '<div class="success-card">🌟 '
                + ("आपकी सोच सही है! बहुत अच्छा।" if lang == "hi"
                   else "Your reasoning is sound! Well done.")
                + "</div>",
                unsafe_allow_html=True,
            )

        elif state == "correct_misconception":
            st.markdown(
                '<div class="misconception-card">⚠️ '
                + ("**संभावित भ्रांति (Possible misconception):** "
                   "उत्तर सही है, लेकिन सोच में एक गलत धारणा दिख रही है।"
                   if lang == "hi" else
                   "**Possible misconception:** Your answer is correct, but the reasoning "
                   "suggests a possible misunderstanding.")
                + "</div>",
                unsafe_allow_html=True,
            )
            if result.evidence_quote:
                st.markdown(
                    f"> *\"{result.evidence_quote}\"*"
                )
            st.markdown(
                '<div class="lesson-card">📖 ' + lesson_text + "</div>",
                unsafe_allow_html=True,
            )

        elif state == "wrong_misconception":
            st.markdown(
                '<div class="misconception-card">⚠️ '
                + ("**संभावित भ्रांति (Possible misconception):**" if lang == "hi"
                   else "**Possible misconception detected:**")
                + "</div>",
                unsafe_allow_html=True,
            )
            if result.evidence_quote:
                st.markdown("**" + ("इस वाक्य में दिखा:" if lang == "hi" else "Evident from:") + "**")
                st.markdown(f"> *\"{result.evidence_quote}\"*")
            st.markdown(
                '<div class="lesson-card">📖 ' + lesson_text + "</div>",
                unsafe_allow_html=True,
            )

        elif state == "wrong_sound":
            st.markdown(
                '<div class="info-card">🤔 '
                + ("आपकी सोच सही लग रही है, लेकिन चुना हुआ उत्तर गलत है। "
                   "क्या आप अपना उत्तर दोबारा जाँचना चाहेंगे?"
                   if lang == "hi" else
                   "Your reasoning sounds valid, but the selected answer is incorrect. "
                   "Would you like to reconsider your selection?")
                + "</div>",
                unsafe_allow_html=True,
            )

        elif state == "clarify_needed":
            st.markdown(
                '<div class="info-card">💬 '
                + ("व्याख्या बहुत कम है। क्या आप थोड़ा और बताएँगे कि आपने कैसे सोचा?"
                   if lang == "hi" else
                   "Your explanation needs a bit more detail. "
                   "Can you describe the step that led to your answer?")
                + "</div>",
                unsafe_allow_html=True,
            )

        else:  # other_reasoning
            st.markdown(
                '<div class="info-card">🔍 '
                + ("आपकी सोच अलग तरह की है। "
                   "हम इसे सामान्य दो भ्रांतियों में नहीं रख सकते। "
                   "नीचे एक checked उदाहरण देखें।"
                   if lang == "hi" else
                   "Your reasoning is different from the two common patterns. "
                   "See the checked example below.")
                + "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="lesson-card">📖 ' + lesson_text + "</div>",
                unsafe_allow_html=True,
            )

        # Fraction visual (from trusted curriculum data)
        render_fraction_visual(question)

        # Optional TTS
        st.markdown("---")
        tts_col1, tts_col2 = st.columns([1, 3])
        with tts_col1:
            if st.button(
                "🔊 सुनें" if lang == "hi" else "🔊 Listen",
                key=f"tts_btn_{question.id}_{st.session_state.attempt_id}",
            ):
                if not api_key:
                    st.warning("API key needed for audio playback.")
                else:
                    with st.spinner("Generating audio…"):
                        try:
                            tts_lang = "hi-IN" if lang == "hi" else "en-IN"
                            tts_text = lesson_text[:400]  # keep short
                            audio_bytes = synthesize_speech(api_key, tts_text, tts_lang)
                            st.session_state.tts_bytes = audio_bytes
                        except SarvamError as exc:
                            st.error(f"Audio unavailable: {exc}")
        if st.session_state.tts_bytes:
            st.audio(st.session_state.tts_bytes, format="audio/wav")

        # Transfer question
        st.markdown("---")
        st.markdown("### " + ("अगला सवाल" if lang == "hi" else "Transfer Question"))

        followup_ids = question.followup_ids
        if followup_ids:
            next_qid = followup_ids[0]
            next_q = get_question(next_qid)
            next_prompt = next_q.prompt_hi if lang == "hi" else next_q.prompt_en
            st.markdown(
                f"**{next_prompt}**\n\n"
                + ("*(उत्तर तब दिखाई देगा जब आप submit करेंगे।)*"
                   if lang == "hi"
                   else "*(The answer will appear after you submit.)*")
            )
            if st.button(
                "➡️ इस सवाल पर जाएँ" if lang == "hi" else "➡️ Go to this question",
                key=f"goto_{next_qid}_{st.session_state.attempt_id}",
            ):
                st.session_state.question_id = next_qid
                reset_question_state()
                st.rerun()
        else:
            st.success(
                "🎉 इस skill के सभी सवाल पूरे हो गए!" if lang == "hi"
                else "🎉 You've completed all questions for this skill!"
            )

    # ── Session history ────────────────────────────────────────────────────────
    if st.session_state.history:
        with st.expander(
            "📋 इस session का इतिहास" if lang == "hi" else "📋 This session's history"
        ):
            st.caption(
                "यह session का डेटा है — कोई mastery estimate नहीं।"
                if lang == "hi"
                else "Session data only — no mastery estimate."
            )
            for i, h in enumerate(reversed(st.session_state.history), 1):
                icon = "✅" if h["correct"] else "❌"
                st.markdown(
                    f"**#{i}** {icon} `{h['question_id']}` · "
                    f"label: `{h['label']}` · "
                    f"_{h['explanation_snippet'][:50]}…_"
                )

    # Footer
    st.markdown(
        '<div class="footer">Created by <strong>Monesh Patidar</strong> · '
        'IIT Kanpur · Powered by Sarvam AI</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
