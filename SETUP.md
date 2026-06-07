# Journalist Helper Setup (v0.2)

> **Important:** This tool currently **only supports MP3 files** (`.mp3` and `.MP3`). It will not detect or process other audio formats such as `.m4a`, `.wav`, `.wma`, `.aac`, etc. See the README for details.

## Reproducing on a New Mac (from Git clone)

This is the recommended way to get a clean, reproducible setup on another machine:

1. Clone the repo:
   ```bash
   git clone https://github.com/ronstauffer/journalist-helper.git
   cd journalist-helper
   ```

2. Run the launch agent installer:
   ```bash
   ./scripts/install-launchd.sh
   ```

3. Grant Full Disk Access (required for the script to read the mounted volume):
   - Go to **System Settings → Privacy & Security → Full Disk Access**
   - Add `/usr/bin/python3` (and optionally the python from `which python3`)

4. Download the Whisper model (if not already present):
   ```bash
   mkdir -p ~/whisper-models && cd ~/whisper-models && whisper-cli --download ggml-medium.en.bin
   ```

5. Plug in your TileTech device. The watcher should automatically detect it and begin processing.

To uninstall the launch agent later:
```bash
launchctl bootout gui/$(id -u)/com.ronstauffer.tiletech-watcher
rm ~/Library/LaunchAgents/com.ronstauffer.tiletech-watcher.plist
```

## Prerequisites (manual setup)
1. Install Homebrew if not already: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. `brew install whisper-cpp ffmpeg`
3. Download Whisper model: `mkdir -p ~/whisper-models && cd ~/whisper-models && whisper-cli --download ggml-medium.en.bin` (or use base/small for faster tests)
4. Make script executable: `chmod +x process_tiletech.py`

## For Auto-Launch on Mount
The easiest way is to use the install script above.

For manual setup (or reference):
- Use macOS Folder Actions or launchd (see the `launchd/` folder for the plist template).
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
