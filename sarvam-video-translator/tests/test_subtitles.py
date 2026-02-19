"""Unit tests for subtitle generation."""

from pathlib import Path

from svt.subtitles import write_srt


def test_single_block_srt(tmp_path: Path):
    out = tmp_path / "test.srt"
    write_srt("Hello world", out, total_duration=10.0)

    content = out.read_text(encoding="utf-8")
    assert "00:00:00,000 --> 00:00:10,000" in content
    assert "Hello world" in content


def test_segmented_srt(tmp_path: Path):
    out = tmp_path / "test.srt"
    segments = [
        {"start": 0.0, "end": 5.0, "text": "First line"},
        {"start": 5.0, "end": 10.0, "text": "Second line"},
    ]
    write_srt("unused", out, segments=segments, total_duration=10.0)

    content = out.read_text(encoding="utf-8")
    assert "First line" in content
    assert "Second line" in content
    assert content.count("-->") == 2
