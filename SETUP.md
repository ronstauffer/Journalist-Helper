# Journalist Helper Setup (v0.2)

> **Important:** This tool currently **only supports MP3 files** (`.mp3` and `.MP3`). It will not detect or process other audio formats such as `.m4a`, `.wav`, `.wma`, `.aac`, etc. See the README for details.

## Prerequisites
1. Install Homebrew if not already: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. `brew install whisper-cpp ffmpeg`
3. Download Whisper model: `mkdir -p ~/whisper-models && cd ~/whisper-models && whisper-cli --download ggml-medium.bin` (or use base/small for faster tests)
4. Make script executable: `chmod +x process_tiletech.py`

## For Auto-Launch on Mount
- Use macOS Folder Actions or launchd.
- For quick test: Plug in TileTech and run `./process_tiletech.py`

## Notifications & Confirmation
- Uses macOS `osascript` for notifications and dialogs.
- Progress via notifications.

Test thoroughly before relying on auto-delete/eject.

## Limitations

- **MP3 files only.** The script scans specifically for `*.MP3` and `*.mp3` files in the recorder's `RECORD` directory. Files in any other format will be skipped entirely.
- Archived output is always given a `.mp3` extension (even if the transcription backend could handle other input formats).

## Next Improvements
- Full filesystem watcher
- Ollama for better summaries
- Better progress during long transcriptions
