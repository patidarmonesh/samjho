# Samjho

### Explain your thinking. Understand your mistake.

**Created by Monesh Patidar — Sole creator and developer**  
**Indian Institute of Technology Kanpur**

Samjho is a Hindi/English fractions tutoring prototype. Learners select
an answer and explain their reasoning by voice or text. The app identifies
a possible misconception, shows a checked visual lesson, and asks a
transfer question.

## Why I built this

An incorrect answer tells a teacher very little about the student's thinking.
Samjho explores how short explanations in a familiar language (Hindi, English,
or Hinglish) can support more targeted conceptual feedback — without needing
a login, database, or full LMS.

## Scope

- Comparing positive fractions with equal numerators (e.g. 1/6 vs 1/8).
- Adding fractions with unlike denominators (e.g. 1/2 + 1/3).
- Six reviewed questions with deterministic Python `Fraction` answer checks.
- Session-based practice; no accounts, no persistent mastery claims.

## Implementation status

- [x] Typed explanation and complete teaching loop
- [x] Evidence-grounded Sarvam reasoning classification (schema-validated)
- [x] Saaras voice transcription with editable transcript confirmation
- [x] Python Fraction answer oracle (never LLM arithmetic)
- [x] Fraction bar SVG visuals from trusted curriculum data only
- [x] Transfer question and session history
- [x] Optional Bulbul lesson playback (on explicit button click)
- [x] Deterministic tests pass (checks, reasoning validation, curriculum oracle)
- [ ] Live API integration — verify after deploying with your key
- [ ] Deployment tested from another browser

## Architecture

```
Audio → Saaras STT → editable transcript ─┐
Typed explanation ────────────────────────┴→ Analyze button
                                              │
                                    Sarvam-M classification
                                              │
                            schema + evidence + skill compatibility checks
                                              │
              Python Fraction oracle  ←── selected answer
                                              │
                         reviewed bilingual lesson + SVG fraction bars
                                              │
                             Transfer question → session history
```

AI interpretation and deterministic answer correctness are kept separate.
Model output is never executed or inserted as raw HTML.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Create `.streamlit/secrets.toml` using the example file:

```toml
SARVAM_API_KEY = "your-key-here"
```

Never commit `secrets.toml` — it is in `.gitignore`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

All deterministic tests (oracle, schema validation, curriculum integrity) pass
without an API key. Live classification cases are run separately.

**Test results (deterministic):** Run `pytest -q` and record the count here.

## Evaluation cases (hand-authored)

| Question | Explanation | Expected label |
|---|---|---|
| compare_01 | "1/8 is larger because 8 is larger than 6." | denominator_size_confusion |
| compare_01 | "8 बड़ा है इसलिए 1/8 बड़ा है।" | denominator_size_confusion |
| compare_01 | "Same whole, six pieces are bigger, so one sixth is larger." | sound_reasoning |
| compare_01 | "1/8." | insufficient_evidence |
| add_01 | "I added 1 and 1, then 2 and 3, so 2/5." | adds_numerators_and_denominators |
| add_01 | "Convert to sixths: 3/6 + 2/6 = 5/6." | sound_reasoning |

Results from live runs to be filled in here after testing.

## Privacy and limitations

Recordings are sent to Sarvam for transcription. Confirmed text is sent for
reasoning analysis. The app does not intentionally persist audio to disk.
Session data is temporary; provider processing is subject to Sarvam's policy.
Avoid personal details in explanations.

This is a bounded prototype. A misconception label is a tentative
interpretation, not a diagnosis. Transcription and classification can be wrong.
The app covers two fraction skills and does not establish long-term mastery or
replace a teacher. No educational effectiveness study has been conducted.

## Author and acknowledgements

**Monesh Patidar** — sole project creator and developer, IIT Kanpur.

Built using:
- [Sarvam AI](https://sarvam.ai/) — speech recognition (Saaras), reasoning classification (Sarvam-M), optional TTS (Bulbul)
- [Streamlit](https://streamlit.io/)
- [Python](https://python.org/) — `fractions`, `wave`, `json`, `unicodedata`
- [Pydantic](https://docs.pydantic.dev/) — strict schema validation
- [requests](https://requests.readthedocs.io/)
- [pytest](https://pytest.org/)

*This project was developed with AI coding assistance. All product decisions,
curriculum design, evaluation cases, validation rules, and architectural
choices are my own.*
