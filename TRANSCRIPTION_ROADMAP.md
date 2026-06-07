# Journalist Helper - Transcription Quality Roadmap

**Status:** Planning document (June 2026)  
**Scope:** Personal use only — no distribution, DMG, or App Store concerns.  
**Core Principle:** The current working version (`process_tiletech.py` + launchd setup) must remain **completely stable and unbroken** at all times. No partial upgrades, no experimental changes merged into the active code until a new version is fully tested and ready to replace it.

## Current State (as of June 2026)

- **Engine**: `whisper.cpp` (via the `whisper-cli` binary from Homebrew/ggml)
- **Model**: `ggml-medium.en.bin` (medium English, quantized)
- **Diarization**: `--tinydiarize` flag + custom `clean_speakers()` heuristic
  - Rule-based labeling (questions → Speaker 1/Interviewer, short answers → Speaker 2, alternating logic)
- **Post-processing**: Basic speaker label cleanup + `extract_gist()` for filenames
- **Strengths**:
  - Fully local and private
  - Runs well on Apple Silicon (Metal backend)
  - Fast enough for the current workflow
  - Works reliably for basic 2-person interview-style audio
- **Limitations** (relative to Descript / Fireflies):
  - Medium model accuracy (more errors on proper names, accents, quiet speech, technical terms)
  - Very basic speaker separation (TinyDiarize is lightweight; struggles with overlaps, >2 speakers, similar voices)
  - Heuristic speaker labeling is brittle
  - Limited naturalness (punctuation, filler words, run-ons, capitalization)
  - No summarization, action items, or higher-level understanding

This is a solid **local personal tool**, but it sits well below commercial services on overall quality and robustness.

## Target Quality

**Goal**: Get as close as possible to Descript / Fireflies quality for **interview-style recordings** (mostly 1–2 speakers, decent audio quality) while staying fully local.

"Close enough" for personal journalist use would include:
- Significantly higher transcription accuracy (closer to large-v3 level)
- Reliable speaker diarization (real speaker embeddings/changes, not just heuristics)
- Better readability (filler removal, natural punctuation, light rephrasing)
- Optional: basic summarization or key-point extraction
- Still fully private and offline (with optional local LLM post-processing)

We will **not** aim for 100% parity on the hardest cases (heavy noise, many overlapping speakers, strong accents). Commercial tools have data and scale advantages there.

## Development Principles (Non-Negotiable)

1. **Current version must always work**  
   The active `process_tiletech.py` + launchd plist + supporting files must remain production-ready for daily use.

2. **No partial upgrades**  
   Do not modify the running script with experimental transcription code. Any upgrade work must be isolated until it is complete, tested on real recordings, and ready to become the new default.

3. **Isolation during development**  
   Recommended approaches:
   - Work on a separate Git branch (`transcription-v2` or similar) and never merge until ready.
   - Or develop in a parallel directory (e.g. `journalist-helper-v2/`) that can be swapped in cleanly.
   - Keep the original launchd plist pointing at the stable version.
   - Consider a simple config flag or separate entry point only after the new version is proven.

4. **Test on real data**  
   Any new version must be validated on actual TileTech recordings (including the kinds of audio you actually record) before it replaces the current one.

5. **Rollback plan**  
   Any switch should be easy to revert (e.g. keep the old script around or use a symlink/versioned launcher).

## Phased Roadmap

### Phase 0 — Current (Stable Baseline)
- `whisper.cpp` + medium model + tinydiarize + heuristic speaker labeling
- Keep this untouched except for bug fixes and the existing robustness improvements (mount waiting, skip-if-already-processed, detailed delete dialog, etc.).

### Phase 1 — Quick Wins (Low-to-Medium Effort, Noticeable Improvement)
**Goal**: Better base accuracy with minimal architecture change.

- Switch from `whisper.cpp` binary to a Python-based engine (`faster-whisper` via CTranslate2 is the usual recommendation for quality + speed on Apple Silicon).
- Upgrade to `large-v3` (or `large-v3-turbo` for better speed/quality tradeoff).
- Improve decoding parameters (larger beam size, better temperature settings, word-level timestamps if useful).
- Optional: Add basic VAD (voice activity detection) preprocessing to trim silence.
- Keep the existing `clean_speakers()` heuristic for now or lightly enhance it.

**Expected impact**: Clear step up in raw transcription quality. Diarization still limited.
**Risk to current version**: None if done in isolation.
**Estimated effort**: 4–12 hours of focused work + testing on real files.

### Phase 2 — Real Diarization + Better Speaker Handling (Medium Effort)
**Goal**: Replace the brittle heuristic speaker labeling with proper diarization.

- Integrate a real diarization backend:
  - `whisperX` (easiest starting point — combines Whisper + alignment + diarization).
  - Or `pyannote.audio` (currently one of the strongest open-source options) + Whisper alignment.
- Feed actual speaker segments into the post-processing instead of (or in addition to) the current question/length rules.
- Improve or replace `clean_speakers()` with something driven by the diarization output.
- Add basic speaker consistency (e.g. remember “Speaker 1” across a single long recording).

**Expected impact**: Much more reliable who-said-what, especially on natural conversation.
**Estimated effort**: 15–35 hours (including learning the diarization library and tuning).

### Phase 3 — LLM Post-Processing & Polish (Medium Effort)
**Goal**: Make the output read much more naturally and add light intelligence.

- Run a local LLM (via Ollama) on the raw Whisper output for:
  - Filler word removal (“um”, “like”, “you know”)
  - Punctuation and capitalization cleanup
  - Light rephrasing for readability while preserving meaning
  - Optional: simple summarization or key points
- Use the LLM + diarization output together to assign more meaningful speaker labels when possible (e.g. “Interviewer” vs actual name inference from context).
- Keep everything local (no cloud calls unless you explicitly want an optional high-quality path later).

**Expected impact**: Transcripts that feel much closer to what Descript produces after its AI cleanup pass.
**Estimated effort**: 10–25 hours (depends heavily on how much prompting/tuning you do).

### Phase 4 — Advanced / Nice-to-Haves (Higher Effort, Diminishing Returns)
- Speaker embedding / voiceprint so the system can recognize the same people across different recordings over time.
- Better long-form handling (chunking + context carry-over for very long interviews).
- Optional noise reduction or audio enhancement step before transcription.
- Structured output (topics, action items, timestamps with speaker turns in a more editable format).
- Simple UI or better logging / review interface (since this is personal use, even a Streamlit or Textual TUI could help).
- Ability to manually correct speakers and have the system learn.
- Hybrid mode: local large model by default + optional one-click send to a cloud service (OpenAI, Grok, etc.) for the most important recordings.

**Estimated effort**: Highly variable (20–100+ hours depending on scope).

## Suggested Development Practices

- **Branching / isolation**:
  - Keep `main` (or the current working directory) as the stable version forever until you decide to cut over.
  - Do all experimentation on a feature branch or in a sibling directory (`journalist-helper-v2/`).
  - Only replace the active `process_tiletech.py` + plist after you have run the new version on multiple real recordings and are happy with it.

- **Configuration**:
  - When ready to experiment, add a simple switch (environment variable, config file, or command-line flag) so you can easily run the old vs. new transcription path during testing.

- **Testing discipline**:
  - Keep a small set of representative recordings (different lengths, noise levels, number of speakers) as a regression test set.
  - Compare old vs. new output on the same files before switching.

- **Rollback**:
  - Always keep the previous working script version around (e.g. `process_tiletech.py.v1` or git tags).

- **Model & dependency management**:
  - Document exact model files and versions used.
  - Because this is personal use, you can keep multiple models around and choose per-run if desired.

## Risks & Considerations

- Larger models (large-v3 etc.) use more RAM/GPU memory and are slower, though your M3 Pro should handle them well.
- Real diarization libraries (especially pyannote) can have setup friction (Hugging Face tokens, model downloads, occasional dependency issues).
- Local LLM post-processing adds another variable — quality depends heavily on the model and prompt you use.
- The more pieces you add (better Whisper + diarization + LLM), the more things can go wrong on any given recording. Plan to keep the current simple path as a reliable fallback.

## Next Steps (When You Have Time)

1. Decide on Phase 1 target (probably switching to `faster-whisper` + large-v3 first).
2. Create an isolated copy/branch for experimentation.
3. Implement and test on real TileTech recordings.
4. Only when satisfied: update the active script + launchd plist, and archive the old version.

---

This document is intended as a living reference. Update it as you learn more during any future work.

**Current working version must stay reliable.** Any future upgrade should be a clean, tested replacement rather than an incremental patch that risks breaking daily use.