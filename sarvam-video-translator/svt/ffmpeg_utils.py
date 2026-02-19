"""Helpers that shell out to ffmpeg / ffprobe."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console(stderr=True)


def ensure_ffmpeg() -> None:
    """Exit with a helpful message if ffmpeg is not on PATH."""
    if shutil.which("ffmpeg") is None:
        console.print(
            "[bold red]Error:[/] ffmpeg not found on PATH.\n"
            "Install it via: brew install ffmpeg  (macOS)\n"
            "               apt install ffmpeg   (Debian/Ubuntu)\n"
            "               choco install ffmpeg  (Windows)"
        )
        sys.exit(1)


def get_duration(video: Path) -> float:
    """Return duration of a media file in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def extract_audio(video: Path, output_wav: Path) -> None:
    """Extract mono 16 kHz WAV from a video file."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    console.print(f"[dim]$ {' '.join(cmd)}[/]")
    subprocess.run(cmd, capture_output=True, check=True)


def extract_audio_chunk(
    video: Path, output_wav: Path, start: float, duration: float
) -> None:
    """Extract a chunk of audio starting at *start* seconds."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(video),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def concat_audio(parts: list[Path], output_wav: Path) -> None:
    """Concatenate WAV files via ffmpeg concat demuxer."""
    list_file = output_wav.with_suffix(".txt")
    list_file.write_text(
        "\n".join(f"file '{p}'" for p in parts), encoding="utf-8"
    )
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    list_file.unlink(missing_ok=True)


def extract_voice_sample(
    video: Path, output_wav: Path, max_duration: float = 90
) -> None:
    """Extract first *max_duration* seconds of audio for voice cloning."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video),
        "-t", str(max_duration),
        "-vn",
        "-ac", "1",
        "-ar", "22050",
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    console.print(f"[dim]$ {' '.join(cmd)}[/]")
    subprocess.run(cmd, capture_output=True, check=True)


def mux_video(
    original_video: Path, dubbed_audio: Path, output_video: Path
) -> None:
    """Replace the audio track of *original_video* with *dubbed_audio*."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(original_video),
        "-i", str(dubbed_audio),
        "-map", "0:v",
        "-map", "1:a",
        "-c:v", "copy",
        "-shortest",
        str(output_video),
    ]
    console.print(f"[dim]$ {' '.join(cmd)}[/]")
    subprocess.run(cmd, capture_output=True, check=True)
