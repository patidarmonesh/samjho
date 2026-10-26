"""
sarvam_client.py — HTTP adapters for Sarvam AI APIs.
Keys stay server-side; no student data is injected into headers/URLs.
"""

import base64
import wave
import io
import requests

BASE_URL = "https://api.sarvam.ai"

# Model constants — change here only
STT_MODEL = "saaras:v2"
CHAT_MODEL = "sarvam-105b"
TTS_MODEL = "bulbul:v1"
TTS_SPEAKER = "anushka"
MAX_AUDIO_SECONDS = 25


class SarvamError(Exception):
    """Raised for all Sarvam API errors with a user-friendly message."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _post(key: str, path: str, **kwargs) -> dict:
    """Core HTTP POST; raises SarvamError on failure."""
    try:
        resp = requests.post(
            BASE_URL + path,
            headers={"api-subscription-key": key},
            timeout=(5, 45),
            **kwargs,
        )
    except requests.exceptions.Timeout:
        raise SarvamError("Request timed out. Please retry.")
    except requests.exceptions.ConnectionError:
        raise SarvamError("Network error. Check your connection.")

    if resp.status_code in (401, 403):
        raise SarvamError(
            "API key not accepted (401/403). Check your Sarvam dashboard.",
            resp.status_code,
        )
    if resp.status_code == 402:
        raise SarvamError(
            "No credits available (402). Please top up your Sarvam account at dashboard.sarvam.ai.",
            resp.status_code,
        )
    if resp.status_code == 429:
        raise SarvamError(
            "Rate limit reached (429). Wait a moment and retry.",
            resp.status_code,
        )
    if resp.status_code == 422:
        raise SarvamError(
            f"Bad request (422): {resp.text[:300]}",
            resp.status_code,
        )
    if resp.status_code >= 500:
        raise SarvamError(
            f"Sarvam server error ({resp.status_code}). Try again later.",
            resp.status_code,
        )
    try:
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise SarvamError(f"Unexpected response: {exc}") from exc


def get_audio_duration_seconds(wav_bytes: bytes) -> float:
    """Return duration of a WAV in seconds using Python's wave module."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return frames / float(rate) if rate > 0 else 0.0
    except Exception:
        return -1.0  # signal invalid/unreadable


def transcribe(key: str, wav_bytes: bytes) -> str:
    """
    Send WAV bytes to Saaras STT; return transcript string.
    Raises SarvamError on failures or oversized audio.
    """
    if len(wav_bytes) < 100:
        raise SarvamError("Audio clip is too short or empty.")

    duration = get_audio_duration_seconds(wav_bytes)
    if duration < 0:
        raise SarvamError("Could not read audio file. Please re-record.")
    if duration > MAX_AUDIO_SECONDS:
        raise SarvamError(
            f"Recording is {duration:.1f}s — maximum is {MAX_AUDIO_SECONDS}s. "
            "Please give a shorter explanation."
        )

    result = _post(
        key,
        "/speech-to-text",
        files={"file": ("reasoning.wav", wav_bytes, "audio/wav")},
        data={
            "model": STT_MODEL,
            "mode": "transcribe",
            "language_code": "unknown",
        },
    )
    transcript = result.get("transcript", "").strip()
    return transcript


def classify_reasoning(key: str, messages: list[dict]) -> str:
    """
    Call Sarvam chat completions; return raw content string.
    Raises SarvamError on failures.
    """
    result = _post(
        key,
        "/v1/chat/completions",
        json={
            "model": CHAT_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
        },
    )
    choices = result.get("choices", [])
    if not choices:
        raise SarvamError("Empty response from classification model.")

    choice = choices[0]
    finish_reason = choice.get("finish_reason", "")
    content = choice.get("message", {}).get("content", "")

    if not content:
        raise SarvamError("Model returned empty content.")
    if finish_reason == "length":
        raise SarvamError(
            "Model response was truncated. Explanation may be too long."
        )
    return content


def synthesize_speech(key: str, text: str, language_code: str = "hi-IN") -> bytes:
    """
    Convert text to speech with Bulbul; return WAV bytes.
    Raises SarvamError on failures.
    """
    result = _post(
        key,
        "/text-to-speech",
        json={
            "inputs": [text],
            "target_language_code": language_code,
            "model": TTS_MODEL,
            "speaker": TTS_SPEAKER,
            "speech_sample_rate": 22050,
            "enable_preprocessing": True,
            "output_audio_codec": "wav",
        },
    )
    audios = result.get("audios", [])
    if not audios or not audios[0]:
        raise SarvamError("TTS returned no audio.")
    try:
        audio_bytes = base64.b64decode(audios[0], validate=True)
    except Exception as exc:
        raise SarvamError(f"Could not decode audio: {exc}") from exc
    if len(audio_bytes) < 100:
        raise SarvamError("TTS audio is empty.")
    return audio_bytes
