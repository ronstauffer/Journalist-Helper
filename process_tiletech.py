#!/usr/bin/env python3
"""
Journalist Helper
Local automation for processing audio from a TileTech recorder.
"""

import os, sys, subprocess, datetime, re, time
from pathlib import Path
import shutil

__version__ = "0.3"

__version__ = "0.3"

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
        
        # Clean tinydiarize artifacts
        line = re.sub(r'\[SPEAKER \d+\]|\[speaker \d+\]', '', orig).strip()
        line = re.sub(r'^-+\s*', '', line).strip()
        
        lower = line.lower()
        
        # Question/command lines → Speaker 1
        if ('?' in line or any(lower.startswith(w) for w in ['what', 'how', 'who', 'when', 'where', 'why', 'can', 'could', 'would', 'speak', 'hey siri', 'recite'])):
            speaker_label = "**Speaker 1 (Interviewer)**: "
            speaker = 2
        # Short answers → Speaker 2
        elif len(line.split()) <= 10 and len(line) < 60:
            speaker_label = "**Speaker 2**: "
        else:
            speaker_label = f"**Speaker {speaker}**: "
            if len(line.split()) > 8:
                speaker = 3 - speaker
        
        cleaned.append(speaker_label + line)
    
    return '\n'.join(cleaned)


def extract_gist(text: str, max_len: int = 55) -> str:
    """Extract a clean filename slug from the first few lines of actual dialogue.
    Strips speaker labels, markdown, slashes, and other unsafe characters.
    """
    if not text or not text.strip():
        return "Conversation"

    # Remove speaker labels we inserted, e.g. "**Speaker 1 (Interviewer)**: " or "**Speaker 2**: "
    label_re = re.compile(r'^\s*\*\*Speaker\s*\d+[^:]*\*\*:\s*', re.IGNORECASE)
    lines = []
    for line in text.splitlines():
        cleaned_line = label_re.sub('', line)
        cleaned_line = re.sub(r'\*\*+', '', cleaned_line)  # leftover bold markers
        # Strip any residual tinydiarize or bare speaker tags that might remain
        cleaned_line = re.sub(r'\[SPEAKER\s*\d+\]', '', cleaned_line, flags=re.IGNORECASE)
        cleaned_line = re.sub(r'\bSpeaker\s*\d+\b', '', cleaned_line, flags=re.IGNORECASE)
        cleaned_line = cleaned_line.strip()
        if cleaned_line:
            lines.append(cleaned_line)

    # Join the first several turns of spoken dialogue
    spoken = ' '.join(lines[:4])

    # Explicitly remove slashes and other filename-dangerous characters
    spoken = spoken.replace('/', ' ').replace('\\', ' ')
    spoken = re.sub(r'[:*?"<>|]', ' ', spoken)

    # Remove apostrophes (what's → whats) without leaving stray spaces, then other punctuation
    spoken = re.sub(r"['’]", '', spoken)
    spoken = re.sub(r"[^a-zA-Z0-9\s\-]", ' ', spoken)
    spoken = re.sub(r'\s+', ' ', spoken).strip()

    # Drop leading numeric artifacts and punctuation (e.g. "18. ", "-Speak", "_foo", "1) ")
    spoken = re.sub(r'^\d+[\s\.\-\)]+\s*', '', spoken)
    spoken = re.sub(r'^[\s\-_.,;:!?]+', '', spoken)

    if not spoken:
        return "Conversation"

    # Build slug from words without exceeding max_len
    words = []
    length = 0
    for w in spoken.split():
        addition = len(w) + (1 if words else 0)
        if length + addition > max_len:
            break
        words.append(w)
        length += addition

    gist = '_'.join(words)
    gist = re.sub(r'_+', '_', gist).strip('_')
    # Final normalization: collapse any mixed separators and trim
    gist = re.sub(r'[-_]+', '_', gist).strip('_')

    return gist or "Conversation"


def main(vol="/Volumes/TILEREC"):
    # Robustness when triggered by launchd on volume mount (e.g. WatchPaths).
    # Volume mount is asynchronous; wait briefly for it to be fully ready.
    if not os.path.exists(vol):
        print(f"[{datetime.datetime.now().isoformat()}] {vol} not present yet, waiting for mount...")
        for i in range(15):  # up to ~15 seconds
            time.sleep(1)
            if os.path.exists(vol):
                print(f"[{datetime.datetime.now().isoformat()}] {vol} detected after waiting.")
                break
        else:
            print(f"[{datetime.datetime.now().isoformat()}] Timeout waiting for {vol}. Nothing to do.")
            return 0

    archive = Path.home() / "Downloads"
    archive.mkdir(parents=True, exist_ok=True)
    
    record_dir = Path(vol) / "RECORD"
    
    def list_record_contents():
        """Return list of names in RECORD, or [] if not accessible."""
        if not record_dir.exists():
            return []
        try:
            return sorted([p.name for p in record_dir.iterdir()])
        except PermissionError as e:
            print(f"  PERMISSION ERROR listing {record_dir}: {e}")
            print("  This is usually fixed by granting Full Disk Access to Python in System Settings > Privacy & Security > Full Disk Access.")
            return []
        except Exception as e:
            print(f"  Error listing {record_dir}: {e}")
            return []
    
    def find_mp3s():
        if not record_dir.exists():
            return []
        try:
            return [p for p in record_dir.iterdir() if p.suffix.upper() == '.MP3']
        except PermissionError as e:
            print(f"  PERMISSION ERROR scanning for MP3s: {e}")
            return []
        except Exception as e:
            print(f"  Error scanning for MP3s: {e}")
            return []
    
    # Extra patience for device files (especially on TileTech) to appear after mount.
    # We poll the directory listing explicitly and log what we see.
    mp3s = find_mp3s()
    
    if not mp3s:
        print(f"[{datetime.datetime.now().isoformat()}] No MP3s visible yet in {record_dir}. Waiting for contents...")
        contents = list_record_contents()
        if contents:
            print(f"  Current RECORD contents: {contents}")
        
        for i in range(30):  # up to 30 seconds of polling
            time.sleep(1)
            mp3s = find_mp3s()
            if mp3s:
                print(f"[{datetime.datetime.now().isoformat()}] Found {len(mp3s)} MP3(s) after {i+1}s additional wait: {[m.name for m in mp3s]}")
                break
            # Log the directory state every few seconds for debugging
            if i % 3 == 0:
                contents = list_record_contents()
                print(f"  Still waiting ({i+1}s)... RECORD contents: {contents}")
        else:
            mp3s = []
            final_contents = list_record_contents()
            print(f"  Final RECORD contents after wait: {final_contents}")
    
    if not mp3s:
        notify("Journalist Helper", "No MP3 files found")
        print("No files found.")
        return 0
    
    notify("Journalist Helper", f"Found {len(mp3s)} files", "Medium model + speaker labels")
    
    newly_processed = []
    
    for i, f in enumerate(mp3s, 1):
        notify("Journalist Helper", f"Processing {i}/{len(mp3s)}", f.name)
        print(f"Processing: {f.name}")
        
        local = archive / f.name
        shutil.copy2(f, local)
        
        model = str(Path.home() / "whisper-models" / "ggml-medium.en.bin")
        
        # Resolve whisper-cli robustly (launchd has very limited PATH)
        whisper_cli = shutil.which("whisper-cli")
        if not whisper_cli:
            for candidate in ("/opt/homebrew/bin/whisper-cli", "/usr/local/bin/whisper-cli"):
                if os.path.exists(candidate):
                    whisper_cli = candidate
                    break
        if not whisper_cli:
            print("Transcription error: whisper-cli not found in PATH or common Homebrew locations")
            continue
        
        try:
            env = os.environ.copy()
            env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + env.get("PATH", "")
            subprocess.run([
                whisper_cli, "-m", model, "-f", str(local),
                "--output-txt", "--language", "en", "--tinydiarize"
            ], check=True, env=env)
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

            # Add version signature so future-you (or anyone) can tell which
            # version of Journalist Helper produced this transcript.
            stamp_date = datetime.datetime.now().strftime("%Y-%m-%d")
            signature = f"\n\n---\nCreated by Journalist Helper v{__version__} on {stamp_date}"
            improved += signature

            with open(transcript_path, 'w', encoding='utf-8') as fh:
                fh.write(improved)
        except Exception as e:
            print("Post-processing error:", e)
        
        # Smart rename
        mtime = datetime.datetime.fromtimestamp(local.stat().st_mtime)
        timestamp = mtime.strftime("%Y-%m-%d_%H-%M")
        
        try:
            with open(transcript_path, encoding='utf-8', errors='ignore') as fh:
                content = fh.read(2000)
            gist = extract_gist(content)
        except Exception as e:
            print("Gist extraction error:", e)
            gist = "Conversation"
        
        new_base = f"{timestamp}_{gist}"
        new_mp3 = archive / f"{new_base}.mp3"
        new_txt = archive / f"{new_base}.txt"
        
        if new_mp3.exists() or new_txt.exists():
            print(f"Skipping {f.name} - already processed as {new_base}")
            # cleanup the temporary copy and transcript created in this run
            if local.exists():
                local.unlink()
            for tmp in list(archive.glob(f"{local.stem}*.txt")):
                if tmp.exists():
                    tmp.unlink()
            continue
        
        local.rename(new_mp3)
        if transcript_path.exists() and transcript_path != new_txt:
            transcript_path.rename(new_txt)
        
        notify("Journalist Helper", f"✅ Completed {i}/{len(mp3s)}", new_base[:50])
        newly_processed.append(f)
    
    if not newly_processed:
        notify("Journalist Helper", "No new files to process")
        # still gracefully eject the device
        time.sleep(2)
        try:
            subprocess.run(["diskutil", "eject", "TILEREC"], check=True, timeout=10)
        except:
            pass
        return 0
    
    # Confirmation + cleanup  (only for files newly processed this run)
    file_list = "\n".join(f.name for f in newly_processed)
    dialog_text = f'All done!\\n\\nDelete these originals from TileTech?\\n\\n{file_list}'
    try:
        result = subprocess.run(
            ["osascript", "-e", f'display dialog "{dialog_text}" buttons {{"No", "Yes"}} default button "Yes"'],
            capture_output=True, text=True
        )
        if "Yes" not in result.stdout:
            notify("Journalist Helper", "Deletion cancelled")
            return 0
    except: pass
    
    for f in newly_processed:
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
