"""Unit tests for sarvam_client – all API calls are mocked."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from svt.config import SarvamConfig
from svt.sarvam_client import speech_to_text, text_to_speech, translate_text


@pytest.fixture()
def cfg() -> SarvamConfig:
    return SarvamConfig(api_key="test-key")


# ── STT ──────────────────────────────────────────────────────────────


def test_speech_to_text_returns_transcript(cfg: SarvamConfig, tmp_path: Path):
    audio = tmp_path / "test.wav"
    audio.write_bytes(b"\x00" * 100)

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "transcript": "hello world",
        "language_code": "en",
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("svt.sarvam_client.httpx.Client") as MockClient:
        MockClient.return_value.__enter__ = MagicMock(return_value=MockClient.return_value)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)
        MockClient.return_value.post.return_value = mock_resp

        result = speech_to_text(cfg, audio, language="en")

    assert result["transcript"] == "hello world"
    assert result["language_code"] == "en"


# ── Translate ────────────────────────────────────────────────────────


def test_translate_text(cfg: SarvamConfig):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"translated_text": "வணக்கம் உலகம்"}
    mock_resp.raise_for_status = MagicMock()

    with patch("svt.sarvam_client.httpx.Client") as MockClient:
        MockClient.return_value.__enter__ = MagicMock(return_value=MockClient.return_value)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)
        MockClient.return_value.post.return_value = mock_resp

        result = translate_text(cfg, "hello world", "en", "ta")

    assert result == "வணக்கம் உலகம்"


# ── TTS ──────────────────────────────────────────────────────────────


def test_text_to_speech_writes_wav(cfg: SarvamConfig, tmp_path: Path):
    out = tmp_path / "out.wav"
    # Return a fake RIFF/WAV so the code writes it directly
    fake_wav = b"RIFF" + b"\x00" * 100
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "audios": [base64.b64encode(fake_wav).decode()]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("svt.sarvam_client.httpx.Client") as MockClient:
        MockClient.return_value.__enter__ = MagicMock(return_value=MockClient.return_value)
        MockClient.return_value.__exit__ = MagicMock(return_value=False)
        MockClient.return_value.post.return_value = mock_resp

        text_to_speech(cfg, "வணக்கம்", "ta", out)

    assert out.exists()
    assert out.read_bytes()[:4] == b"RIFF"
