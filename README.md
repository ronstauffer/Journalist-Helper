# Journalist Helper

**MP3-only (current limitation).**

macOS automation for TileTech recorder MP3s: auto-process on mount, transcribe with local Whisper, rename intelligently, notify progress, confirm before cleanup, and eject.

**v0.2** — Added notifications, progress alerts, user confirmation, auto-eject.

## Limitations

- **Only works with MP3 files.** The script explicitly looks for `*.mp3` and `*.MP3` files on the recorder volume. Other formats (`.m4a`, `.wav`, `.wma`, `.aac`, etc.) are ignored and will not be processed.
- Output files are always saved with a `.mp3` extension.
- The underlying transcription engine (whisper.cpp + ffmpeg) can handle other formats, but the discovery, processing, and renaming logic is currently MP3-specific only.

Clone: `git clone https://github.com/ronstauffer/journalist-helper.git`

See [SETUP.md](SETUP.md) for full installation instructions, including how to set up automatic launch on device mount using the included launch agent.

The `launchd/` folder contains the plist template and `scripts/install-launchd.sh` makes fresh-machine setup straightforward.
