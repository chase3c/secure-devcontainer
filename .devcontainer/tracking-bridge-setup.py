#!/usr/bin/env python3
"""Container-side hook installer for Claude Code session tracking.

Run from postStartCommand to register tracking hooks in the container's
~/.claude/settings.json. Idempotent — skips if hooks already present.

Usage in devcontainer.json postStartCommand:
  python3 /workspace/.devcontainer/tracking-bridge-setup.py
"""
import json
import os

SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
# Default location — override via CLAUDE_TRACKING_BRIDGE_SCRIPT env var
BRIDGE_SCRIPT = os.environ.get(
    "CLAUDE_TRACKING_BRIDGE_SCRIPT",
    "/workspace/.devcontainer/tracking-bridge.py",
)

HOOK_COMMAND = f"python3 {BRIDGE_SCRIPT}"

# Hook events to track, with per-event options
HOOK_EVENTS = {
    "UserPromptSubmit": {"timeout": 5},
    "PostToolUse": {"timeout": 5},
    "Stop": {"timeout": 5},
    "PermissionRequest": {"timeout": 5},
    "SessionEnd": {"timeout": 5},
}


def install_hooks():
    settings = {}
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH) as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    hooks = settings.get("hooks", {})
    changed = False

    # Clean up old-format entries and stale events from previous versions
    for event in list(hooks.keys()):
        event_entries = hooks[event]
        cleaned = [
            entry for entry in event_entries
            if not (
                isinstance(entry, dict)
                and entry.get("command") == HOOK_COMMAND
            )
        ]
        if len(cleaned) != len(event_entries):
            hooks[event] = cleaned
            changed = True
        # Remove empty event lists
        if not hooks[event]:
            del hooks[event]
            changed = True

    for event, opts in HOOK_EVENTS.items():
        event_entries = hooks.get(event, [])
        # Check if our hook is already registered (in the matcher/hooks format)
        already = any(
            isinstance(entry, dict)
            and any(
                h.get("command") == HOOK_COMMAND
                for h in entry.get("hooks", [])
            )
            for entry in event_entries
        )
        if not already:
            hook_def = {"type": "command", "command": HOOK_COMMAND}
            hook_def.update(opts)
            event_entries.append({"hooks": [hook_def]})
            hooks[event] = event_entries
            changed = True

    if changed:
        settings["hooks"] = hooks
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=2)
        print(f"[claude-tracking] Hooks installed in {SETTINGS_PATH}")
    else:
        print("[claude-tracking] Hooks already installed, skipping")


if __name__ == "__main__":
    install_hooks()
