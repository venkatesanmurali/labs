# Sarvam Video Translator

CLI tool that takes an input video and produces a dubbed version in a target Indian language using [Sarvam AI](https://www.sarvam.ai/) APIs.

## How it works

```
Input video
  │
  ▼
┌──────────────┐
│ ffmpeg       │  extract mono 16 kHz WAV
└──────┬───────┘
       ▼
┌──────────────┐
│ Sarvam STT   │  speech → text (source language)
└──────┬───────┘
       ▼
┌──────────────┐
│ Sarvam       │  translate text → target language
│ Translate    │
└──────┬───────┘
       ▼
┌──────────────┐
│ Sarvam TTS   │  text → speech (target language)
└──────┬───────┘
       ▼
┌──────────────┐
│ ffmpeg       │  replace audio track in original video
└──────┬───────┘
       ▼
Output video (dubbed)
```

For videos longer than 10 minutes the audio is automatically chunked, processed in parts, and stitched back together.

## Prerequisites

- **Python 3.10+**
- **ffmpeg** installed and on your PATH
  ```bash
  # macOS
  brew install ffmpeg
  # Debian / Ubuntu
  sudo apt install ffmpeg
  ```
- A **Sarvam AI API key** — sign up at <https://www.sarvam.ai/>

## Installation

```bash
cd sarvam-video-translator
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Configuration

Copy the example env file and add your key:

```bash
cp .env.example .env
# edit .env and set SARVAM_API_KEY
```

If Sarvam's endpoint paths or model names change, override them in `.env` (see `.env.example` for all options).

## Usage

```bash
# Translate an English video to Tamil
python -m svt translate --input input.mp4 --target ta --output output_ta.mp4

# Specify source language explicitly
python -m svt translate -i input.mp4 -t hi -s en -o output_hi.mp4

# Generate subtitles alongside the video
python -m svt translate -i input.mp4 -t te --subtitles

# Dry run (no API calls, just prints the plan)
python -m svt translate -i input.mp4 -t kn --dry-run

# Use a specific TTS voice
python -m svt translate -i input.mp4 -t ta --voice meera
```

### Supported languages

`en` `hi` `ta` `te` `kn` `ml` `bn` `mr` `gu` `pa` `or`

Use `--source auto` (the default) to let Sarvam detect the source language.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

## Quick demo (30-second clip)

```bash
# 1. Record or download a short 30s clip (e.g. someone speaking English)
# 2. Place it as demo.mp4 in this directory
# 3. Run:
python -m svt translate -i demo.mp4 -t ta -o demo_ta.mp4 --subtitles
# 4. Play demo_ta.mp4 — the audio is now in Tamil
#    and demo_ta.srt contains Tamil subtitles.
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ffmpeg not found on PATH` | Install ffmpeg (see Prerequisites) |
| `SARVAM_API_KEY is not set` | Copy `.env.example` to `.env` and add your key |
| `API call failed after 3 attempts` | Check your API key, network, and Sarvam service status |
| `unsupported format '.avi'` | Convert to mp4 first: `ffmpeg -i in.avi out.mp4` |
| Unicode garbled in subtitles | Ensure your text editor / player uses UTF-8 |
| Output audio shorter than video | The `--shortest` flag trims to the shorter track; TTS output length depends on the translated text |

## Project structure

```
sarvam-video-translator/
├── svt/
│   ├── __init__.py
│   ├── __main__.py      # python -m svt entry point
│   ├── cli.py            # argument parsing
│   ├── config.py          # env-based configuration
│   ├── ffmpeg_utils.py    # audio extraction & muxing
│   ├── pipeline.py        # orchestration
│   ├── sarvam_client.py   # Sarvam API wrapper
│   └── subtitles.py       # SRT generation
├── tests/
│   ├── test_sarvam_client.py
│   └── test_subtitles.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## License

MIT
