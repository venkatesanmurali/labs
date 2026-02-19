"""
Orchestration pipeline: extract → transcribe → translate → TTS → mux.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from rich.console import Console

from svt import elevenlabs_client as el
from svt import ffmpeg_utils as ff
from svt import google_client as google
from svt import sarvam_client as api
from svt.config import (
    CHUNK_MAX_SECONDS,
    ElevenLabsConfig,
    SarvamConfig,
    is_indian_lang,
)
from svt.subtitles import write_srt

console = Console(stderr=True)


def run(
    input_video: Path,
    target_lang: str,
    output_video: Path,
    source_lang: str = "auto",
    voice: str | None = None,
    subtitles: bool = False,
    dry_run: bool = False,
    clone_voice: bool = False,
) -> None:
    cfg = SarvamConfig()
    el_cfg = ElevenLabsConfig()

    if not cfg.api_key and is_indian_lang(target_lang):
        console.print(
            "[bold red]Error:[/] SARVAM_API_KEY is not set.\n"
            "Export it or add it to a .env file in the current directory."
        )
        raise SystemExit(1)

    if clone_voice and not el_cfg.api_key:
        console.print(
            "[bold red]Error:[/] ELEVENLABS_API_KEY is not set.\n"
            "--clone-voice requires an ElevenLabs API key.\n"
            "Export it or add it to a .env file in the current directory."
        )
        raise SystemExit(1)

    ff.ensure_ffmpeg()

    console.print(f"[bold]Input:[/]  {input_video}")
    console.print(f"[bold]Output:[/] {output_video}")
    console.print(f"[bold]Target language:[/] {target_lang}")
    if clone_voice:
        console.print("[bold]Voice cloning:[/] enabled (ElevenLabs)")

    if dry_run:
        provider = "Sarvam" if is_indian_lang(target_lang) else "Google"
        tts_provider = "ElevenLabs (cloned voice)" if clone_voice else provider
        console.print("\n[yellow][DRY RUN][/] Steps that would execute:")
        console.print("  1. Extract audio from video (ffmpeg)")
        if clone_voice:
            console.print("  1.5. Extract voice sample for cloning (ffmpeg)")
            console.print("  1.6. Clone voice via ElevenLabs")
        console.print("  2. Transcribe audio via Sarvam STT")
        console.print(f"  3. Translate transcript via {provider}")
        console.print(f"  4. Synthesise translated text via {tts_provider}")
        console.print("  5. Mux synthesised audio back into video (ffmpeg)")
        if clone_voice:
            console.print("  5.5. Delete cloned voice from ElevenLabs")
        if subtitles:
            console.print("  6. Write .srt subtitle file")
        return

    tmpdir = Path(tempfile.mkdtemp(prefix="svt_"))
    try:
        _run_pipeline(
            cfg, input_video, target_lang, output_video,
            source_lang, voice, subtitles, tmpdir,
            clone_voice=clone_voice, el_cfg=el_cfg,
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_pipeline(
    cfg: SarvamConfig,
    input_video: Path,
    target_lang: str,
    output_video: Path,
    source_lang: str,
    voice: str | None,
    subtitles: bool,
    tmpdir: Path,
    clone_voice: bool = False,
    el_cfg: ElevenLabsConfig | None = None,
) -> None:
    cloned_voice_id: str | None = None

    try:
        # 1 ── Extract audio ──────────────────────────────────────────
        console.print("\n[bold cyan]Step 1/5[/] Extracting audio …")
        duration = ff.get_duration(input_video)
        console.print(f"  Video duration: {duration:.1f}s")

        need_chunking = duration > CHUNK_MAX_SECONDS
        if need_chunking:
            transcript, detected_lang = _chunked_stt(
                cfg, input_video, source_lang, duration, tmpdir
            )
        else:
            extracted = tmpdir / "extracted.wav"
            ff.extract_audio(input_video, extracted)
            transcript, detected_lang = _single_stt(
                cfg, extracted, source_lang
            )

        console.print(f"  Transcript ({len(transcript)} chars): {transcript[:120]}…")

        # 1.5 ── Voice cloning ────────────────────────────────────────
        if clone_voice and el_cfg:
            console.print("\n[bold cyan]Step 1.5[/] Extracting voice sample …")
            voice_sample = tmpdir / "voice_sample.wav"
            ff.extract_voice_sample(input_video, voice_sample)
            console.print("  Voice sample extracted.")

            console.print("\n[bold cyan]Step 1.6[/] Cloning voice via ElevenLabs …")
            cloned_voice_id = el.add_voice(
                el_cfg,
                name=f"svt_clone_{input_video.stem}",
                audio_path=voice_sample,
            )
            console.print(f"  Voice cloned (id: {cloned_voice_id})")

        # 3 ── Translate ──────────────────────────────────────────────
        src = detected_lang if source_lang == "auto" else source_lang
        use_sarvam = is_indian_lang(target_lang)
        provider = "Sarvam" if use_sarvam else "Google"
        console.print(
            f"\n[bold cyan]Step 3/5[/] Translating {src} → {target_lang} "
            f"via {provider} …"
        )
        if use_sarvam:
            translated = api.translate_text(cfg, transcript, src, target_lang)
        else:
            translated = google.translate_text(transcript, src, target_lang)
        console.print(f"  Translated ({len(translated)} chars): {translated[:120]}…")

        # 4 ── TTS ────────────────────────────────────────────────────
        if clone_voice and cloned_voice_id and el_cfg:
            console.print(
                "\n[bold cyan]Step 4/5[/] Synthesising speech via "
                "ElevenLabs (cloned voice) …"
            )
            dubbed_wav = tmpdir / "dubbed.wav"
            el.text_to_speech(
                el_cfg, translated, cloned_voice_id, dubbed_wav,
                language_code=target_lang,
            )
        else:
            console.print(
                f"\n[bold cyan]Step 4/5[/] Synthesising speech via {provider} …"
            )
            dubbed_wav = tmpdir / "dubbed.wav"
            if use_sarvam:
                api.text_to_speech(
                    cfg, translated, target_lang, dubbed_wav, voice=voice
                )
            else:
                google.text_to_speech(translated, target_lang, dubbed_wav)
        console.print("  Audio generated.")

        # 5 ── Mux ────────────────────────────────────────────────────
        console.print("\n[bold cyan]Step 5/5[/] Muxing dubbed audio into video …")
        ff.mux_video(input_video, dubbed_wav, output_video)
        console.print(f"\n[bold green]Done![/] Output saved to {output_video}")

        # Optional: subtitles
        if subtitles:
            srt_path = output_video.with_suffix(".srt")
            write_srt(translated, srt_path, total_duration=duration)
            console.print(f"  Subtitles saved to {srt_path}")

    finally:
        # Always clean up the cloned voice
        if cloned_voice_id and el_cfg:
            try:
                console.print("\n[dim]Cleaning up cloned voice …[/]")
                el.delete_voice(el_cfg, cloned_voice_id)
                console.print("[dim]  Cloned voice deleted.[/]")
            except Exception:
                console.print(
                    f"[yellow]Warning:[/] Failed to delete cloned voice "
                    f"{cloned_voice_id}. Delete it manually from your "
                    f"ElevenLabs dashboard."
                )


# ── Revoice pipeline ─────────────────────────────────────────────────


def revoice(
    original_video: Path,
    translated_video: Path,
    output_video: Path,
    target_lang: str,
    dry_run: bool = False,
) -> None:
    """Re-synthesise the translated video's audio using the original speaker's voice."""
    cfg = SarvamConfig()
    el_cfg = ElevenLabsConfig()

    if not el_cfg.api_key:
        console.print(
            "[bold red]Error:[/] ELEVENLABS_API_KEY is not set.\n"
            "Export it or add it to a .env file in the current directory."
        )
        raise SystemExit(1)

    ff.ensure_ffmpeg()

    console.print(f"[bold]Original (voice source):[/] {original_video}")
    console.print(f"[bold]Translated (text source):[/] {translated_video}")
    console.print(f"[bold]Output:[/] {output_video}")
    console.print(f"[bold]Language:[/] {target_lang}")

    if dry_run:
        console.print("\n[yellow][DRY RUN][/] Steps that would execute:")
        console.print("  1. Extract voice sample from original video (ffmpeg)")
        console.print("  2. Clone voice via ElevenLabs")
        console.print("  3. Extract & transcribe translated video audio (Sarvam STT)")
        console.print("  4. Re-synthesise transcript with cloned voice (ElevenLabs TTS)")
        console.print("  5. Mux new audio into translated video (ffmpeg)")
        console.print("  6. Delete cloned voice from ElevenLabs")
        return

    tmpdir = Path(tempfile.mkdtemp(prefix="svt_revoice_"))
    cloned_voice_id: str | None = None

    try:
        # 1 ── Extract voice sample from original ─────────────────────
        console.print("\n[bold cyan]Step 1/5[/] Extracting voice sample from original …")
        voice_sample = tmpdir / "voice_sample.wav"
        ff.extract_voice_sample(original_video, voice_sample)
        console.print("  Voice sample extracted.")

        # 2 ── Clone voice ────────────────────────────────────────────
        console.print("\n[bold cyan]Step 2/5[/] Cloning voice via ElevenLabs …")
        cloned_voice_id = el.add_voice(
            el_cfg,
            name=f"svt_revoice_{original_video.stem}",
            audio_path=voice_sample,
        )
        console.print(f"  Voice cloned (id: {cloned_voice_id})")

        # 3 ── Transcribe translated video ────────────────────────────
        console.print("\n[bold cyan]Step 3/5[/] Transcribing translated video …")
        duration = ff.get_duration(translated_video)
        extracted = tmpdir / "translated_audio.wav"
        ff.extract_audio(translated_video, extracted)
        result = api.speech_to_text(cfg, extracted, target_lang)
        transcript = result.get("transcript", "")
        console.print(f"  Transcript ({len(transcript)} chars): {transcript[:120]}…")

        # 4 ── TTS with cloned voice ──────────────────────────────────
        console.print("\n[bold cyan]Step 4/5[/] Synthesising with cloned voice …")
        dubbed_wav = tmpdir / "dubbed.wav"
        el.text_to_speech(
            el_cfg, transcript, cloned_voice_id, dubbed_wav,
            language_code=target_lang,
        )
        console.print("  Audio generated.")

        # 5 ── Mux ────────────────────────────────────────────────────
        console.print("\n[bold cyan]Step 5/5[/] Muxing into video …")
        ff.mux_video(translated_video, dubbed_wav, output_video)
        console.print(f"\n[bold green]Done![/] Output saved to {output_video}")

    finally:
        if cloned_voice_id:
            try:
                console.print("\n[dim]Cleaning up cloned voice …[/]")
                el.delete_voice(el_cfg, cloned_voice_id)
                console.print("[dim]  Cloned voice deleted.[/]")
            except Exception:
                console.print(
                    f"[yellow]Warning:[/] Failed to delete cloned voice "
                    f"{cloned_voice_id}. Delete it manually from your "
                    f"ElevenLabs dashboard."
                )
        shutil.rmtree(tmpdir, ignore_errors=True)


# ── helpers ──────────────────────────────────────────────────────────


def _single_stt(
    cfg: SarvamConfig, audio: Path, language: str
) -> tuple[str, str]:
    """Run STT on a single audio file. Return (transcript, detected_lang)."""
    console.print("\n[bold cyan]Step 2/5[/] Transcribing audio …")
    result = api.speech_to_text(cfg, audio, language)
    transcript = result.get("transcript", "")
    detected = result.get("language_code", language)
    return transcript, detected


def _chunked_stt(
    cfg: SarvamConfig,
    video: Path,
    language: str,
    duration: float,
    tmpdir: Path,
) -> tuple[str, str]:
    """Split audio into chunks, transcribe each, and concatenate."""
    console.print("\n[bold cyan]Step 2/5[/] Transcribing audio (chunked) …")
    chunks: list[str] = []
    detected = language
    offset = 0.0
    idx = 0
    while offset < duration:
        chunk_wav = tmpdir / f"chunk_{idx}.wav"
        ff.extract_audio_chunk(video, chunk_wav, offset, CHUNK_MAX_SECONDS)
        result = api.speech_to_text(cfg, chunk_wav, language)
        chunks.append(result.get("transcript", ""))
        if idx == 0:
            detected = result.get("language_code", language)
        offset += CHUNK_MAX_SECONDS
        idx += 1
        console.print(f"  Chunk {idx} transcribed.")

    return " ".join(chunks), detected
