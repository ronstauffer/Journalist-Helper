# Journalist Helper Setup

## Prerequisites
1. Install Homebrew if not installed: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
2. `brew install whisper-cpp ffmpeg`
3. Download Whisper model: `mkdir -p ~/whisper-models && whisper-cli --download ggml-medium.en.bin` (or similar; check whisper-cpp docs)
4. Create directories: `mkdir -p ~/Recordings/TileTech/Processed`

## Install the Script
```bash
cd ~
git clone https://github.com/ronstauffer/Journalist-Helper.git
cd Journalist-Helper
chmod +x process_tiletech.py
```

## Manual Test
Plug in TileTech and run:
```bash
python3 process_tiletech.py /Volumes/TileTech
```

## Auto-launch (Folder Actions or launchd)
See Automator section in full docs (to be expanded).

Update volume name if your TileTech mounts differently.