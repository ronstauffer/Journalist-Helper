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

## How it works & Design notes (important for future maintainers or future-you)

The system is deliberately kept simple and the **current working version must remain stable**. All the logic lives in one script (`process_tiletech.py`) that is triggered by a launch agent.

**Core flow when you plug in the device:**
1. The launchd agent (watching `/Volumes`) starts the script.
2. The script waits for `/Volumes/TILEREC` to appear (mounts can be slow/asynchronous).
3. It then polls `RECORD/` for a while and prints what it sees (this debug output goes to `/tmp/tiletech-watcher.log`). This was added because the directory contents are sometimes not immediately visible to the launched process even after the volume path exists (timing + macOS privacy restrictions).
4. When MP3s are found it copies them locally, transcribes with local Whisper, applies speaker labeling, generates a gist from the transcript, and renames both the MP3 and TXT.
5. **Important safety rule**: If a file with the same final name already exists in `~/Downloads`, the script skips it (prints "Skipping ... already processed") and does **not** delete the original from the device. Only files that were actually newly processed in this run are offered for deletion.
6. At the end it shows a dialog listing the *exact* files it wants to delete from the TileTech (not a generic "delete originals?"). If you say No it still ejects the device.

**Why certain things are the way they are:**
- We watch `/Volumes` (not the specific TILEREC path) + poll the contents because direct WatchPaths on a removable volume is unreliable.
- The script is intentionally chatty in the watcher log when things are slow or failing — the "Still waiting... RECORD contents: [...]" lines are there on purpose for debugging.
- Deletion is deliberately conservative (only newly processed files, explicit list in the dialog) because you may have chosen not to delete some files in a previous run.
- The current version is treated as a stable baseline. Future improvements (better models, real diarization, etc.) are meant to be developed in isolation so this working version is never left in a half-broken state.

## Notifications & Confirmation
- Uses macOS `osascript` for notifications and dialogs.
- Progress via notifications.

Test thoroughly before relying on auto-delete/eject.

## Limitations

- **MP3 files only.** The script scans specifically for `*.MP3` and `*.mp3` files in the recorder's `RECORD` directory. Files in any other format will be skipped entirely.
- Archived output is always given a `.mp3` extension (even if the transcription backend could handle other input formats).

## Troubleshooting / FAQ

This section covers the most common problems we've hit while building and using the tool.

**"Operation not permitted" when trying to read /Volumes/TILEREC/RECORD**

This is the most common error during development. It means macOS is blocking the Python process (launched by the background agent) from accessing the removable volume.

**Fix:**
- Go to **System Settings → Privacy & Security → Full Disk Access**
- Add `/usr/bin/python3` (unlock the padlock first)
- You may need to unload/reload the launch agent afterward:
  ```bash
  launchctl bootout gui/$(id -u)/com.ronstauffer.tiletech-watcher 2>/dev/null || true
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ronstauffer.tiletech-watcher.plist
  ```

**Script runs (or the watcher fires) but says "No files found" even though `ls /Volumes/TILEREC/RECORD/` shows .MP3 files**

The volume can appear before the `RECORD` folder contents are fully visible to the process (especially right after plugging in). The script now waits and logs what it actually sees.

**What to do:**
- Check the log: `tail -f /tmp/tiletech-watcher.log`
- Look for lines like `Still waiting (Xs)... RECORD contents: [...]` or `Error listing...`
- If you see the MP3 filenames in the log but the script still says no files, wait a bit longer or re-plug.
- The script now has extended patience (up to ~45 seconds total) for this reason.

**Nothing happens when I plug in the device (no notifications, no log activity)**

**Check:**
1. Is the launch agent loaded?
   ```bash
   launchctl list | grep tiletech-watcher
   ```
2. Tail the log while plugging in:
   ```bash
   tail -f /tmp/tiletech-watcher.log
   ```
3. Make sure the install script was run on this machine (see "Reproducing on a New Mac").

**The same files keep getting processed every time I plug in**

This was a common issue before we added the "already processed" check. The current version should now skip files whose final renamed versions already exist in `~/Downloads`.

If it's still re-processing:
- Check that the renamed `.mp3` and `.txt` pairs really exist in `~/Downloads`.
- The skip only works after the gist has been computed (i.e. after transcription), so you may see some repeated work in the log, but it should clean up the temps and not overwrite the final files.

**I see a lot of "No files found." lines in the log with no timestamps**

These are usually from the script being triggered multiple times by the watcher during a single plug/unplug cycle (normal behavior). The timestamped lines are the ones from the current improved version.

**The delete dialog lists files I don't want to delete**

That's exactly why we made the dialog list the exact filenames now. Just click "No" — the device will still be ejected, but nothing will be deleted from the TileTech. You can always delete manually later if you want.

## Next Improvements
- Full filesystem watcher
- Ollama for better summaries
- Better progress during long transcriptions
