"""
Thin wrapper around Sarvam AI REST APIs.

Endpoints, models, and voices are pulled from SarvamConfig so they can
be overridden via env vars or a .env file.
"""

from __future__ import annotations

import base64
import time
import wave
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console

from svt.config import SarvamConfig, to_bcp47

console = Console(stderr=True)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def _headers(cfg: SarvamConfig) -> dict[str, str]:
    return {
        "api-subscription-key": cfg.api_key,
    }


def _url(cfg: SarvamConfig, endpoint: str) -> str:
    return f"{cfg.base_url.rstrip('/')}{endpoint}"


def _retry(fn, *args, **kwargs) -> Any:  # noqa: ANN401
    """Call *fn* with exponential back-off on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            detail = ""
            if isinstance(exc, httpx.HTTPStatusError):
                detail = f" — {exc.response.status_code}: {exc.response.text[:200]}"
            console.print(f"[red]API error{detail}[/]")
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                console.print(
                    f"[yellow]Retry {attempt}/{MAX_RETRIES} in {wait}s …[/]"
                )
                time.sleep(wait)
    raise RuntimeError(
        f"API call failed after {MAX_RETRIES} attempts"
    ) from last_exc


# ── Speech-to-Text ───────────────────────────────────────────────────


def speech_to_text(
    cfg: SarvamConfig,
    audio_path: Path,
    language: str = "auto",
) -> dict[str, Any]:
    """
    Send an audio file to Sarvam STT and return the JSON response.

    Expected response shape:
      { "transcript": "...", "language_code": "hi-IN", ... }
    """

    def _call() -> dict[str, Any]:
        bcp47 = to_bcp47(language)
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/wav")}
            data: dict[str, str] = {"model": cfg.stt_model}
            data["language_code"] = bcp47
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    _url(cfg, cfg.stt_endpoint),
                    headers=_headers(cfg),
                    files=files,
                    data=data,
                )
                resp.raise_for_status()
                return resp.json()

    return _retry(_call)


# ── Translation ──────────────────────────────────────────────────────


def translate_text(
    cfg: SarvamConfig,
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """Translate *text* and return the translated string."""

    def _call() -> str:
        payload = {
            "input": text,
            "source_language_code": to_bcp47(source_lang),
            "target_language_code": to_bcp47(target_lang),
            "model": cfg.translate_model,
            "enable_preprocessing": True,
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                _url(cfg, cfg.translate_endpoint),
                headers={**_headers(cfg), "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()["translated_text"]

    return _retry(_call)


# ── Text-to-Speech ───────────────────────────────────────────────────


def text_to_speech(
    cfg: SarvamConfig,
    text: str,
    target_lang: str,
    output_path: Path,
    voice: str | None = None,
) -> None:
    """
    Convert *text* to speech and write the result to *output_path* (WAV).
    """
    speaker = voice or cfg.tts_default_voice

    def _call() -> None:
        payload = {
            "text": text,
            "target_language_code": to_bcp47(target_lang),
            "model": cfg.tts_model,
            "speaker": speaker,
            "speech_sample_rate": 22050,
            "output_audio_codec": "wav",
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                _url(cfg, cfg.tts_endpoint),
                headers={**_headers(cfg), "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # Sarvam TTS returns base64-encoded audio in "audios" list
        audio_b64 = data["audios"][0]
        audio_bytes = base64.b64decode(audio_b64)

        # If Sarvam returns a complete WAV, detect by magic bytes.
        if audio_bytes[:4] == b"RIFF":
            output_path.write_bytes(audio_bytes)
        else:
            # Raw PCM fallback — wrap in WAV header
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                wf.writeframes(audio_bytes)

    _retry(_call)
