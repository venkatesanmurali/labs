"""Command-line interface for Sarvam Video Translator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from svt.config import SUPPORTED_LANGUAGES, SUPPORTED_VIDEO_FORMATS
from svt.pipeline import revoice, run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="svt",
        description="Translate and dub a video into another language using Sarvam AI.",
    )
    sub = parser.add_subparsers(dest="command")

    tr = sub.add_parser("translate", help="Translate a video file")
    tr.add_argument(
        "--input", "-i", required=True, type=Path,
        help="Path to the input video (mp4/mkv/mov).",
    )
    tr.add_argument(
        "--target", "-t", required=True, choices=SUPPORTED_LANGUAGES[1:],
        help="Target language code (e.g. ta, hi, te).",
    )
    tr.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output video path. Default: <input>_<target>.mp4",
    )
    tr.add_argument(
        "--source", "-s", default="auto", choices=SUPPORTED_LANGUAGES,
        help="Source language code or 'auto' (default: auto).",
    )
    tr.add_argument(
        "--voice", default=None,
        help="TTS voice/speaker name (optional; defaults per language).",
    )
    tr.add_argument(
        "--subtitles", action="store_true",
        help="Generate an .srt subtitle file alongside the output.",
    )
    tr.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without calling any APIs.",
    )
    tr.add_argument(
        "--clone-voice", action="store_true",
        help="Clone the original speaker's voice via ElevenLabs for TTS.",
    )
    # ── revoice subcommand ─────────────────────────────────────────
    rv = sub.add_parser(
        "revoice",
        help="Re-synthesise a translated video using the original speaker's voice.",
    )
    rv.add_argument(
        "--original", required=True, type=Path,
        help="Path to the original video (voice source).",
    )
    rv.add_argument(
        "--input", "-i", required=True, type=Path,
        help="Path to the translated video (text source).",
    )
    rv.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output video path. Default: <input>_revoiced.mp4",
    )
    rv.add_argument(
        "--lang", "-l", required=True, choices=SUPPORTED_LANGUAGES[1:],
        help="Language of the translated video (for STT + TTS).",
    )
    rv.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without calling any APIs.",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "translate":
        _handle_translate(args)
    elif args.command == "revoice":
        _handle_revoice(args)
    else:
        parser.print_help()
        sys.exit(0)


def _validate_video(path: Path) -> Path:
    """Resolve and validate a video file path."""
    resolved = path.resolve()
    if not resolved.is_file():
        print(f"Error: input file not found: {resolved}", file=sys.stderr)
        sys.exit(1)
    if resolved.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
        print(
            f"Error: unsupported format '{resolved.suffix}'. "
            f"Supported: {', '.join(SUPPORTED_VIDEO_FORMATS)}",
            file=sys.stderr,
        )
        sys.exit(1)
    return resolved


def _handle_translate(args: argparse.Namespace) -> None:
    input_video = _validate_video(args.input)

    output_video: Path = args.output or input_video.with_stem(
        f"{input_video.stem}_{args.target}"
    )
    output_video = output_video.resolve()

    run(
        input_video=input_video,
        target_lang=args.target,
        output_video=output_video,
        source_lang=args.source,
        voice=args.voice,
        subtitles=args.subtitles,
        dry_run=args.dry_run,
        clone_voice=args.clone_voice,
    )


def _handle_revoice(args: argparse.Namespace) -> None:
    original_video = _validate_video(args.original)
    translated_video = _validate_video(args.input)

    output_video: Path = args.output or translated_video.with_stem(
        f"{translated_video.stem}_revoiced"
    )
    output_video = output_video.resolve()

    revoice(
        original_video=original_video,
        translated_video=translated_video,
        output_video=output_video,
        target_lang=args.lang,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
