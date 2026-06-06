#/usr/bin/env python3
"""
Journalist Helper v0.2
Enhanced with notifications, progress, confirmation, and auto-eject.
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path
import shutil
import time
import re

def notify(title, message, subtitle=""):
    """Send macOS notification"""
    script = f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
    subprocess.run(["osascript", "-e", script])

def get_progress(current, total):
    """Simple progress percentage"""
    return int((current / total) * 100) if total > 0 else 0

def main(volume_path="/Volumes/TileTech"):
    archive_dir = Path.home() / "Recordings" / "TileTech" / "Processed"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    notify("Journalist Helper", "Drive mounted. Checking for files...", "Starting processing")
    
    if not os.path.isdir(volume_path):
        notify("Journalist Helper", "No TileTech volume found.", "Error")
        print("No TileTech volume found.")
        return 0
    
    mp3_files = list(Path(volume_path).rglob("*.mp3"))
    if not mp3_files:
        notify("Journalist Helper", "No MP3 files found.", "Nothing to process")
        print("No MP3 files found.")
        return 0
    
    notify("Journalist Helper", f"Found {len(mp3_files)} files. Starting processing...", f"Total: {len(mp3_files)}")
    
    for idx, mp3_path in enumerate(mp3_files, 1):
        print(f"Processing {idx}/{len(mp3_files)}: {mp3_path.name}")
        notify("Journalist Helper", f"Processing file {idx}/{len(mp3_files)}", mp3_path.name)
        
        # Copy to archive
        local_mp3 = archive_dir / mp3_path.name
        shutil.copy2(mp3_path, local_mp3)
        notify("Journalist Helper", "Copied to archive", f"{idx}/{len(mp3_files)}")
        
        # Transcribe
        transcript_path = local_mp3.with_suffix('.txt')
        model_path = str(Path.home() / "whisper-models" / "ggml-medium.bin")  # Adjust path
        
        notify("Journalist Helper", f"Transcribing {idx}/{len(mp3_files)}...", "This may take a minute")
        try:
            result = subprocess.run([
                "whisper-cli", "-m", model_path, "-f", str(local_mp3),
                "--output-txt", "--language", "en"
            ], capture_output=True, text=True, check=True)
            print(result.stdout)
        except Exception as e:
            notify("Journalist Helper", f"Transcription failed for file {idx}", str(e))
            print(f"⚠️ Transcription failed: {e}")
            continue
        
        # Timestamp and gist
        mtime = datetime.datetime.fromtimestamp(local_mp3.stat().st_mtime)
        timestamp = mtime.strftime("%Y-%m-%d_%H%M")
        
        with open(transcript_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(500)
        gist_raw = re.sub(r'[^a-zA-Z0-9 -_]', '', content.splitlines()[0][:80]).strip().replace(' ', '_')[:50] or "Conversation"
        gist = re.sub(r'_+', '_', gist_raw).strip('_')
        
        new_base = f"{timestamp}_{gist}"
        new_mp3 = archive_dir / f"{new_base}.mp3"
        new_txt = archive_dir / f"{new_base}.txt"
        
        local_mp3.rename(new_mp3)
        if transcript_path.exists():
            transcript_path.rename(new_txt)
        
        notify("Journalist Helper", f"File {idx}/{len(mp3_files)} ready", new_base)
    
    # Confirmation before delete
    confirm_script = '''
    set dialogResult to display dialog "All files processed and renamed. Confirm deletion from TileTech?" buttons {"No", "Yes"} default button "Yes"
    return button returned of dialogResult
    '''
    try:
        confirm = subprocess.run(["osascript", "-e", confirm_script], capture_output=True, text=True).stdout.strip()
        if confirm != "Yes":
            notify("Journalist Helper", "Deletion cancelled by user.", "Files preserved on device")
            return 0
    except:
        print("Confirmation failed, skipping delete.")
        return 0
    
    # Delete from source
    for mp3_path in mp3_files:
        if mp3_path.exists():
            mp3_path.unlink()
    notify("Journalist Helper", "Files deleted from TileTech.", "Cleanup complete")
    
    # Auto-eject
    try:
        volume_name = Path(volume_path).name
        subprocess.run(["diskutil", "eject", volume_name], check=True)
        notify("Journalist Helper", "TileTech ejected successfully.", "All done!")
    except Exception as e:
        notify("Journalist Helper", "Eject failed. Please eject manually.", str(e))
    
    notify("Journalist Helper", "Processing complete!", f"{len(mp3_files)} files handled.")
    print("🎉 All files processed and device ejected.")
    return 0

if __name__ == "__main__":
    vol = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/TileTech"
    sys.exit(main(vol))
