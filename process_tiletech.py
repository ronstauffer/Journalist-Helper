#!/usr/bin/env python3
import os, sys, subprocess, datetime
from pathlib import Path
import shutil, re, glob

def notify(t, m, s=""):
    try:
        subprocess.run(["osascript", "-e", f'display notification "{m}" with title "{t}" subtitle "{s}" sound name "Glass"'])
    except: pass

def main(vol="/Volumes/TILEREC"):
    # Changed save location to Downloads
    archive = Path.home() / "Downloads"
    archive.mkdir(parents=True, exist_ok=True)
    
    record_dir = Path(vol) / "RECORD"
    mp3s = list(record_dir.glob("*.MP3")) + list(record_dir.glob("*.mp3")) if record_dir.exists() else []
    
    if not mp3s:
        notify("Journalist Helper", "No MP3 files found")
        print("No files found.")
        return 0
    
    notify("Journalist Helper", f"Found {len(mp3s)} files", "Saving to Downloads...")
    
    for i, f in enumerate(mp3s, 1):
        notify("Journalist Helper", f"Processing {i}/{len(mp3s)}", f.name)
        print(f"Processing: {f.name}")
        
        local = archive / f.name
        shutil.copy2(f, local)
        
        model = str(Path.home() / "whisper-models" / "ggml-base.en.bin")
        
        try:
            subprocess.run([
                "whisper-cli", "-m", model, "-f", str(local),
                "--output-txt", "--language", "en"
            ], check=True)
        except Exception as e:
            print("Transcription error:", e)
            continue
        
        # Find transcript
        txt_files = list(archive.glob(f"{local.stem}*.txt"))
        transcript_path = txt_files[0] if txt_files else local.with_suffix('.txt')
        
        mtime = datetime.datetime.fromtimestamp(local.stat().st_mtime)
        timestamp = mtime.strftime("%Y-%m-%d_%H%M")
        
        try:
            with open(transcript_path, encoding='utf-8', errors='ignore') as fh:
                content = fh.read(600)
            gist_raw = re.sub(r'[^a-zA-Z0-9 -_]', '', (content.splitlines()[0] if content else "")[:80]).strip().replace(' ', '_')[:45] or "Conversation"
            gist = re.sub(r'_+', '_', gist_raw).strip('_')
        except:
            gist = "Conversation"
        
        new_base = f"{timestamp}_{gist}"
        new_mp3 = archive / f"{new_base}.mp3"
        new_txt = archive / f"{new_base}.txt"
        
        local.rename(new_mp3)
        if transcript_path.exists() and transcript_path != new_txt:
            transcript_path.rename(new_txt)
        
        notify("Journalist Helper", f"✅ Completed {i}/{len(mp3s)}", new_base[:50])
    
    try:
        result = subprocess.run(["osascript", "-e", 'display dialog "All done!\n\nDelete originals from TileTech?" buttons {"No", "Yes"} default button "Yes"'], capture_output=True, text=True)
        if "Yes" not in result.stdout:
            notify("Journalist Helper", "Deletion cancelled")
            return 0
    except: pass
    
    for f in mp3s:
        if f.exists():
            f.unlink()
    
    try:
        subprocess.run(["diskutil", "eject", "TILEREC"], check=True)
        notify("Journalist Helper", "✅ All done & ejected!")
    except:
        notify("Journalist Helper", "Done - eject manually")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
