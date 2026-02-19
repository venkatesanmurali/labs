"""Unit tests for google_client – all external calls are mocked."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from svt.google_client import text_to_speech, translate_text


# ── Translate ────────────────────────────────────────────────────────


def test_translate_text_french():
    with patch("svt.google_client.GoogleTranslator") as MockTranslator:
        instance = MockTranslator.return_value
        instance.translate.return_value = "Bonjour le monde"

        result = translate_text("Hello world", "en", "fr")

    MockTranslator.assert_called_once_with(source="en", target="fr")
    instance.translate.assert_called_once_with("Hello world")
    assert result == "Bonjour le monde"


def test_translate_text_auto_source():
    with patch("svt.google_client.GoogleTranslator") as MockTranslator:
        instance = MockTranslator.return_value
        instance.translate.return_value = "Hola mundo"

        result = translate_text("Hello world", "auto", "es")

    MockTranslator.assert_called_once_with(source="auto", target="es")
    assert result == "Hola mundo"


# ── TTS ──────────────────────────────────────────────────────────────


def test_text_to_speech_writes_wav(tmp_path: Path):
    out = tmp_path / "out.wav"
    mp3_path = out.with_suffix(".mp3")

    with (
        patch("svt.google_client.gTTS") as MockGTTS,
        patch("svt.google_client._mp3_to_wav") as mock_convert,
    ):
        tts_instance = MockGTTS.return_value
        # Simulate gTTS.save creating the mp3 file
        tts_instance.save.side_effect = lambda p: Path(p).write_bytes(b"fake-mp3")

        # Simulate _mp3_to_wav creating the wav file
        mock_convert.side_effect = lambda src, dst: dst.write_bytes(
            b"RIFF" + b"\x00" * 100
        )

        text_to_speech("Bonjour", "fr", out)

    MockGTTS.assert_called_once_with(text="Bonjour", lang="fr")
    tts_instance.save.assert_called_once_with(str(mp3_path))
    mock_convert.assert_called_once_with(mp3_path, out)


def test_text_to_speech_german(tmp_path: Path):
    out = tmp_path / "out.wav"

    with (
        patch("svt.google_client.gTTS") as MockGTTS,
        patch("svt.google_client._mp3_to_wav"),
    ):
        tts_instance = MockGTTS.return_value
        tts_instance.save.side_effect = lambda p: Path(p).write_bytes(b"fake")

        text_to_speech("Hallo Welt", "de", out)

    MockGTTS.assert_called_once_with(text="Hallo Welt", lang="de")
