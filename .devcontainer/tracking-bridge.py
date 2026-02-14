#!/usr/bin/env python3
"""Container-side hook script for Claude Code session tracking.

Standalone script (no dependencies beyond stdlib) that reads Claude hook
events from stdin and appends them to a JSONL bridge file in the workspace.
The host-side server watches for these files and imports events into the
tracking DB.

Usage in container hooks:
  python3 /workspace/.devcontainer/tracking-bridge.py
"""
import json
import os
import sys
import time
import socket
BRIDGE_DIR = "/workspace/.claude-tracking-bridge"
BRIDGE_FILE = os.path.join(BRIDGE_DIR, "events.jsonl")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    host_dir = os.environ.get("CLAUDE_TRACKING_HOST_DIR", "")
    host_tmux_pane = os.environ.get("CLAUDE_TRACKING_HOST_TMUX_PANE", "")
    container_name = socket.gethostname()

    event = {
        "timestamp": time.time(),
        "container": container_name,
        "host_dir": host_dir,
        "host_tmux_pane": host_tmux_pane,
        "data": data,
    }

    os.makedirs(BRIDGE_DIR, exist_ok=True)

    line = json.dumps(event, separators=(",", ":")) + "\n"

    # Atomic-ish append: open in append mode
    fd = os.open(BRIDGE_FILE, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        os.write(fd, line.encode())
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
