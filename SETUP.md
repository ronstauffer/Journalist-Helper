# Journalist Helper Setup (v0.2)

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

## Next Improvements
- Full filesystem watcher
- Ollama for better summaries
- Better progress during long transcriptions
