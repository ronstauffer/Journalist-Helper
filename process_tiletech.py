#!/usr/bin/env python3
"""
Journalist Helper v0.1
Processes TileTech MP3s: copy, transcribe, rename, clean.
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path
import shutil

def main(volume_path="/Volumes/TileTech"):
    archive_dir = Path.home() / "Recordings" / "TileTech" / "Processed"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📰 Journalist Helper: Checking {volume_path}")
    
    if not os.path.isdir(volume_path):
        print("No TileTech volume found.")
        return 0
    
    mp3_files = list(Path(volume_path).rglob("*.mp3"))
    for mp3_path in mp3_files:
        print(f"Processing: {mp3_path.name}")
        
        # Copy to archive
        local_mp3 = archive_dir / mp3_path.name
        shutil.copy2(mp3_path, local_mp3)
        
        # Transcribe (whisper.cpp)
        transcript_path = local_mp3.with_suffix('.txt')
        model_path = str(Path.home() / "whisper-models" / "ggml-medium.bin")  # Adjust if needed
        try:
            subprocess.run([
                "whisper-cli", "-m", model_path, "-f", str(local_mp3),
                "--output-txt", "--language", "en"
            ], check=True, capture_output=True)
            print("Transcription complete.")
        except Exception as e:
            print(f"⚠️ Transcription failed: {e}. Continuing...")
            continue
        
        # Timestamp from file
        mtime = datetime.datetime.fromtimestamp(local_mp3.stat().st_mtime)
        timestamp = mtime.strftime("%Y-%m-%d_%H%M")
        
        # Basic gist from start of transcript
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(400)  # First ~400 chars
        gist = ''.join(c for c in content.splitlines()[0][:80] if c.isalnum() or c in ' -_')[:50].strip().replace(' ', '_') or "Conversation"
        
        new_base = f"{timestamp}_{gist}"
        new_mp3 = archive_dir / f"{new_base}.mp3"
        new_txt = archive_dir / f"{new_base}.txt"
        
        local_mp3.rename(new_mp3)
        if transcript_path.exists():
            transcript_path.rename(new_txt)
        
        # Delete from TileTech
        mp3_path.unlink()
        print(f"✅ Done: {new_base}")
    
    print("🎉 All files processed.")
    return 0

if __name__ == "__main__":
    vol = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/TileTech"
    sys.exit(main(vol))
