#!/bin/bash
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$REPO_DIR/launchd/com.ronstauffer.tiletech-watcher.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.ronstauffer.tiletech-watcher.plist"

if [ ! -f "$PLIST_SRC" ]; then
  echo "Error: Could not find plist template at $PLIST_SRC"
  exit 1
fi

echo "Installing TileTech watcher launch agent..."
echo "Repo location: $REPO_DIR"

# Copy and replace placeholder
sed "s|{{REPO_PATH}}|$REPO_DIR|g" "$PLIST_SRC" > "$PLIST_DST"

# Unload if already loaded (ignore errors)
launchctl bootout gui/$(id -u)/com.ronstauffer.tiletech-watcher 2>/dev/null || true

# Load the new one
launchctl bootstrap gui/$(id -u) "$PLIST_DST"

echo ""
echo "Launch agent installed and loaded."
echo ""
echo "Next steps:"
echo "  1. Make sure you have granted Full Disk Access to /usr/bin/python3"
echo "     (System Settings → Privacy & Security → Full Disk Access)"
echo "  2. Download the Whisper model if you haven't:"
echo "     mkdir -p ~/whisper-models && cd ~/whisper-models && whisper-cli --download ggml-medium.en.bin"
echo "  3. Plug in your TileTech device to test."
echo ""
echo "To uninstall later:"
echo "  launchctl bootout gui/$(id -u)/com.ronstauffer.tiletech-watcher"
echo "  rm \"$PLIST_DST\""
