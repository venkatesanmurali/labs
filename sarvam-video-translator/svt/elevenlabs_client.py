"""
Thin wrapper around ElevenLabs REST APIs for voice cloning and TTS.

Uses the same retry / httpx patterns as sarvam_client.py.
"""

from __future__ import annotations

import time
import wave
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console

from svt.config import ElevenLabsConfig

console = Console(stderr=True)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def _headers(cfg: ElevenLabsConfig) -> dict[str, str]:
    return {"xi-api-key": cfg.api_key}


def _url(cfg: ElevenLabsConfig, path: str) -> str:
    return f"{cfg.base_url.rstrip('/')}{path}"


def _retry(fn, *args, **kwargs) -> Any:  # noqa: ANN401
    """Call *fn* with exponential back-off on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE ** attempt
                console.print(
                    f"[yellow]Retry {attempt}/{MAX_RETRIES} in {wait}s …[/]"
                )
                time.sleep(wait)
    raise RuntimeError(
        f"ElevenLabs API call failed after {MAX_RETRIES} attempts"
    ) from last_exc


# ── Voice Cloning ─────────────────────────────────────────────────────


def add_voice(
    cfg: ElevenLabsConfig,
    name: str,
    audio_path: Path,
    remove_bg_noise: bool = True,
) -> str:
    """
    Create an instant voice clone from *audio_path*.

    Returns the voice_id assigned by ElevenLabs.
    """

    def _call() -> str:
        with open(audio_path, "rb") as f:
            # httpx needs a list of tuples for multipart fields
            files_data = [
                ("name", (None, name)),
                ("remove_background_noise", (None, str(remove_bg_noise).lower())),
                ("files", (audio_path.name, f, "audio/wav")),
            ]
            with httpx.Client(timeout=120) as client:
                resp = client.post(
                    _url(cfg, "/v1/voices/add"),
                    headers=_headers(cfg),
                    files=files_data,
                )
                if resp.status_code >= 400:
                    console.print(f"[red]ElevenLabs error: {resp.text}[/]")
                resp.raise_for_status()
                return resp.json()["voice_id"]

    return _retry(_call)


# ── Text-to-Speech ───────────────────────────────────────────────────


def text_to_speech(
    cfg: ElevenLabsConfig,
    text: str,
    voice_id: str,
    output_path: Path,
    language_code: str | None = None,
    model_id: str | None = None,
    stability: float = 0.75,
    similarity_boost: float = 1.0,
    style: float = 0.0,
    use_speaker_boost: bool = True,
) -> None:
    """
    Convert *text* to speech using a cloned voice and write to *output_path* (WAV).

    Voice settings tuned for maximum similarity to the original speaker:
    - similarity_boost=1.0 : stick as close to original voice as possible
    - stability=0.75      : consistent tone, low variation
    - style=0.0           : no stylistic exaggeration
    - use_speaker_boost=True : extra similarity processing
    """
    model = model_id or cfg.model_id

    def _call() -> None:
        payload: dict[str, Any] = {
            "text": text,
            "model_id": model,
            "output_format": "pcm_22050",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost,
            },
        }
        if language_code:
            payload["language_code"] = language_code
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                _url(cfg, f"/v1/text-to-speech/{voice_id}"),
                headers={**_headers(cfg), "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            audio_bytes = resp.content

        # ElevenLabs pcm_22050 returns raw PCM — wrap in WAV header
        with wave.open(str(output_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(audio_bytes)

    _retry(_call)


# ── Voice Deletion ───────────────────────────────────────────────────


def delete_voice(cfg: ElevenLabsConfig, voice_id: str) -> None:
    """Delete a cloned voice by its *voice_id*."""

    def _call() -> None:
        with httpx.Client(timeout=30) as client:
            resp = client.delete(
                _url(cfg, f"/v1/voices/{voice_id}"),
                headers=_headers(cfg),
            )
            resp.raise_for_status()

    _retry(_call)
