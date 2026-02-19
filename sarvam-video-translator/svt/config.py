"""
Centralised configuration.

Every value can be overridden via environment variables or a .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from CWD (or project root) if present
load_dotenv(Path.cwd() / ".env")


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class SarvamConfig:
    api_key: str = field(default_factory=lambda: _env("SARVAM_API_KEY"))

    base_url: str = field(
        default_factory=lambda: _env(
            "SARVAM_BASE_URL", "https://api.sarvam.ai"
        )
    )

    # ── Endpoints (relative to base_url) ─────────────────────────────
    # Adjust these if Sarvam changes their API paths.
    stt_endpoint: str = field(
        default_factory=lambda: _env(
            "SARVAM_STT_ENDPOINT", "/speech-to-text"
        )
    )
    translate_endpoint: str = field(
        default_factory=lambda: _env(
            "SARVAM_TRANSLATE_ENDPOINT", "/translate"
        )
    )
    tts_endpoint: str = field(
        default_factory=lambda: _env(
            "SARVAM_TTS_ENDPOINT", "/text-to-speech"
        )
    )

    # ── Model / voice IDs ────────────────────────────────────────────
    stt_model: str = field(
        default_factory=lambda: _env("SARVAM_STT_MODEL", "saarika:v2.5")
    )
    translate_model: str = field(
        default_factory=lambda: _env(
            "SARVAM_TRANSLATE_MODEL", "mayura:v1"
        )
    )
    tts_model: str = field(
        default_factory=lambda: _env("SARVAM_TTS_MODEL", "bulbul:v3")
    )

    # Default TTS voice (user can override via CLI --voice)
    tts_default_voice: str = field(
        default_factory=lambda: _env("SARVAM_TTS_VOICE", "shubh")
    )


# Short code → BCP-47 mapping (Sarvam uses BCP-47 format)
LANG_CODE_MAP: dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "gu": "gu-IN",
    "pa": "pa-IN",
    "or": "od-IN",  # Sarvam uses "od-IN" for Odia
}

# Indian languages handled by Sarvam
INDIAN_LANGUAGES: set[str] = {
    "en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa", "or",
}

# European languages handled by Google Translate + gTTS
# Maps our short code → gTTS / deep-translator language code
EUROPEAN_LANGUAGES: dict[str, str] = {
    "fr": "fr",  # French
    "es": "es",  # Spanish
    "de": "de",  # German
    "pt": "pt",  # Portuguese
    "it": "it",  # Italian
    "nl": "nl",  # Dutch
}

# CLI-facing short codes
SUPPORTED_LANGUAGES = [
    "auto", "en", "hi", "ta", "te", "kn", "ml", "bn", "mr", "gu", "pa", "or",
    "fr", "es", "de", "pt", "it", "nl",
]


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str = field(default_factory=lambda: _env("ELEVENLABS_API_KEY"))

    base_url: str = field(
        default_factory=lambda: _env(
            "ELEVENLABS_BASE_URL", "https://api.elevenlabs.io"
        )
    )

    model_id: str = field(
        default_factory=lambda: _env(
            "ELEVENLABS_MODEL", "eleven_multilingual_v2"
        )
    )


def is_indian_lang(code: str) -> bool:
    """Return True if *code* is an Indian language handled by Sarvam."""
    return code in INDIAN_LANGUAGES


def to_bcp47(short: str) -> str:
    """Convert a short language code to Sarvam's BCP-47 format."""
    if short == "auto":
        return "unknown"
    return LANG_CODE_MAP.get(short, short)

SUPPORTED_VIDEO_FORMATS = {".mp4", ".mkv", ".mov"}

# Chunking threshold in seconds
CHUNK_MAX_SECONDS = 600  # 10 minutes
