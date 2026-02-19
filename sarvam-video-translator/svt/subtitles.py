"""Simple SRT subtitle generation."""

from __future__ import annotations

from pathlib import Path


def _fmt_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(
    text: str,
    output: Path,
    segments: list[dict] | None = None,
    total_duration: float = 30.0,
) -> None:
    """
    Write an .srt file.

    If *segments* with start/end timestamps are available, use them.
    Otherwise create a single subtitle block spanning the full duration.
    """
    lines: list[str] = []

    if segments:
        for idx, seg in enumerate(segments, 1):
            start = seg.get("start", 0.0)
            end = seg.get("end", total_duration)
            txt = seg.get("text", text)
            lines.append(str(idx))
            lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
            lines.append(txt.strip())
            lines.append("")
    else:
        lines.append("1")
        lines.append(f"{_fmt_ts(0)} --> {_fmt_ts(total_duration)}")
        lines.append(text.strip())
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
