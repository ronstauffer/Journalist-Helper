# Journalist Helper

A macOS automation for processing TileTech recorder MP3 files.

## Features
- Detects when TileTech USB device mounts.
- Copies MP3 files to local archive.
- Transcribes using local Whisper (whisper.cpp recommended for Apple Silicon).
- Generates summary/gist from transcription.
- Renames files: `YYYY-MM-DD_HHMM_GistOfConversation.mp3` + matching `.txt`
- Deletes originals from TileTech after success.

## Setup
See SETUP.md

## Development
Built with Grok. Iterate and improve!