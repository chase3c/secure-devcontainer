#!/usr/bin/env python3
"""Container-side setup for Claude Code configuration.

Run from postStartCommand to configure:
  - Session tracking hooks in ~/.claude/settings.json
  - Status line (command-based, reads from statusline.sh)

Idempotent — skips settings that are already present.

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
STATUSLINE_SCRIPT = "/workspace/.devcontainer/statusline.sh"

HOOK_COMMAND = f"python3 {BRIDGE_SCRIPT}"
BEANS_COMMAND = "beans prime"

# Hook events to track, with per-event options
HOOK_EVENTS = {
    "UserPromptSubmit": {"timeout": 5},
    "PostToolUse": {"timeout": 5},
    "Stop": {"timeout": 5},
    "PermissionRequest": {"timeout": 5},
    "SessionEnd": {"timeout": 5},
}

# Beans hooks — inject task context at session start and before compaction
BEANS_HOOK_EVENTS = {
    "SessionStart": {"timeout": 10},
    "PreCompact": {"timeout": 10},
}


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def install_hooks(settings):
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
        print(f"[claude-setup] Tracking hooks installed")
    else:
        print("[claude-setup] Tracking hooks already installed, skipping")

    return changed


def install_beans_hooks(settings):
    hooks = settings.get("hooks", {})
    changed = False

    for event, opts in BEANS_HOOK_EVENTS.items():
        event_entries = hooks.get(event, [])
        already = any(
            isinstance(entry, dict)
            and any(
                h.get("command") == BEANS_COMMAND
                for h in entry.get("hooks", [])
            )
            for entry in event_entries
        )
        if not already:
            hook_def = {"type": "command", "command": BEANS_COMMAND}
            hook_def.update(opts)
            event_entries.append({"hooks": [hook_def]})
            hooks[event] = event_entries
            changed = True

    if changed:
        settings["hooks"] = hooks
        print("[claude-setup] Beans hooks installed")
    else:
        print("[claude-setup] Beans hooks already installed, skipping")

    return changed


def install_statusline(settings):
    expected = {"type": "command", "command": STATUSLINE_SCRIPT}
    current = settings.get("statusLine")
    if current == expected:
        print("[claude-setup] Status line already configured, skipping")
        return False

    settings["statusLine"] = expected
    print("[claude-setup] Status line configured")
    return True


if __name__ == "__main__":
    settings = load_settings()
    hooks_changed = install_hooks(settings)
    beans_changed = install_beans_hooks(settings)
    statusline_changed = install_statusline(settings)
    if hooks_changed or beans_changed or statusline_changed:
        save_settings(settings)
        print(f"[claude-setup] Settings written to {SETTINGS_PATH}")
