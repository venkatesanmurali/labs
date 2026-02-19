"""
Wrapper around deep-translator (Google Translate) and gTTS for European languages.
"""

from __future__ import annotations

from pathlib import Path

from deep_translator import GoogleTranslator
from gtts import gTTS

from svt.config import EUROPEAN_LANGUAGES


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Translate *text* using Google Translate via deep-translator."""
    # deep-translator uses 'auto' for auto-detection, and standard ISO codes
    src = "auto" if source_lang == "auto" else _to_google_code(source_lang)
    tgt = _to_google_code(target_lang)
    return GoogleTranslator(source=src, target=tgt).translate(text)


def text_to_speech(text: str, target_lang: str, output_path: Path) -> None:
    """Convert *text* to speech using gTTS and write a WAV-compatible file."""
    lang_code = _to_google_code(target_lang)
    tts = gTTS(text=text, lang=lang_code)
    # gTTS writes MP3; save as .mp3 then let ffmpeg handle conversion in pipeline
    # Actually, write directly — ffmpeg mux step can handle mp3 input too.
    mp3_path = output_path.with_suffix(".mp3")
    tts.save(str(mp3_path))
    # Convert MP3 → WAV so the rest of the pipeline stays consistent
    _mp3_to_wav(mp3_path, output_path)
    mp3_path.unlink(missing_ok=True)


def _to_google_code(short: str) -> str:
    """Map our short code to Google's language code."""
    if short in EUROPEAN_LANGUAGES:
        return EUROPEAN_LANGUAGES[short]
    # For Indian language codes used as source (e.g. 'hi', 'en'), pass through
    return short


def _mp3_to_wav(mp3_path: Path, wav_path: Path) -> None:
    """Convert MP3 to WAV using ffmpeg."""
    import subprocess

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(mp3_path),
            "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
    )
