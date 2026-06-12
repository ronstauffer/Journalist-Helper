#!/usr/bin/env python3
import os, sys, subprocess, datetime, re, time
from pathlib import Path
import shutil

def notify(t, m, s=""):
    try:
        subprocess.run(["osascript", "-e", f'display notification "{m}" with title "{t}" subtitle "{s}" sound name "Glass"'])
    except: pass

def clean_speakers(text):
    lines = text.split('\n')
    cleaned = []
    speaker = 1  # 1 = Interviewer, 2 = Interviewee

    for line in lines:
        orig = line.strip()
        if not orig:
            cleaned.append("")
            continue

        # Clean artifacts
        line = re.sub(r'\[SPEAKER \d+\]|\[speaker \d+\]', '', orig).strip()
        line = re.sub(r'^-+\s*', '', line).strip()

        lower = line.lower()

        if ('?' in line or any(lower.startswith(w) for w in ['what', 'how', 'who', 'when', 'where', 'why', 'can', 'could', 'would', 'speak', 'hey siri', 'recite'])):
            speaker_label = "**Speaker 1 (Interviewer)**: "
            speaker = 2
        elif len(line.split()) <= 10 and len(line) < 60:
            speaker_label = "**Speaker 2**: "
        else:
            speaker_label = f"**Speaker {speaker}**: "
            if len(line.split()) > 8:
                speaker = 3 - speaker

        cleaned.append(speaker_label + line)

    return '\n'.join(cleaned)

def main(vol="/Volumes/TILEREC"):
    archive = Path.home() / "Downloads"
    archive.mkdir(parents=True, exist_ok=True)

    record_dir = Path(vol) / "RECORD"
    mp3s = list(record_dir.glob("*.MP3")) + list(record_dir.glob("*.mp3")) if record_dir.exists() else []

    if not mp3s:
        notify("Journalist Helper", "No MP3 files found")
        print("No files found.")
        return 0

    notify("Journalist Helper", f"Found {len(mp3s)} files", "Medium model + speaker labels")

    for i, f in enumerate(mp3s, 1):
        notify("Journalist Helper", f"Processing {i}/{len(mp3s)}", f.name)
        print(f"Processing: {f.name}")

        local = archive / f.name
        shutil.copy2(f, local)

        model = str(Path.home() / "whisper-models" / "ggml-medium.en.bin")

        try:
            subprocess.run([
                "whisper-cli", "-m", model, "-f", str(local),
                "--output-txt", "--language", "en", "--tinydiarize"
            ], check=True)
        except Exception as e:
            print("Transcription error:", e)
            continue

        # Find transcript
        txt_files = list(archive.glob(f"{local.stem}*.txt"))
        transcript_path = txt_files[0] if txt_files else local.with_suffix('.txt')

        # Improve speaker labels
        try:
            with open(transcript_path, encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
            improved = clean_speakers(content)
            with open(transcript_path, 'w', encoding='utf-8') as fh:
                fh.write(improved)
        except Exception as e:
            print("Post-processing error:", e)

        # Smart rename
        mtime = datetime.datetime.fromtimestamp(local.stat().st_mtime)
        timestamp = mtime.strftime("%Y-%m-%d_%H%M")

        try:
            with open(transcript_path, encoding='utf-8', errors='ignore') as fh:
                content = fh.read(800)
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

    # Safer confirmation
    notify("Journalist Helper", "Processing complete", "Review files in Downloads")
    time.sleep(3)

    try:
        result = subprocess.run([
            "osascript", "-e",
            'display dialog "All done!\n\nDelete originals from TileTech?" buttons {"No", "Yes"} default button "No"'
        ], capture_output=True, text=True)

        if "Yes" not in result.stdout:
            notify("Journalist Helper", "Deletion cancelled by user")
            return 0
    except:
        notify("Journalist Helper", "Confirmation skipped")
        return 0

    for f in mp3s:
        if f.exists():
            f.unlink()

    # Graceful eject
    time.sleep(2)
    try:
        subprocess.run(["diskutil", "eject", "TILEREC"], check=True, timeout=10)
        notify("Journalist Helper", "✅ All done & ejected!")
    except:
        notify("Journalist Helper", "Done - eject manually if needed")

    return 0

if __name__ == "__main__":
    sys.exit(main())