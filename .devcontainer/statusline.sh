#!/bin/bash
# Claude Code status line — shows model, project, git branch, context usage.
# Reads JSON from stdin (provided by Claude Code).
input=$(cat)

# Colors
PURPLE='\033[35m'
BLUE='\033[34m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

# Extract values
MODEL=$(echo "$input" | jq -r '.model.display_name')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir')
PERCENT_USED=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)

# Git info
GIT_INFO=""
if git -C "$CURRENT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git -C "$CURRENT_DIR" branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
        # Truncate long branch names
        if [ ${#BRANCH} -gt 20 ]; then
            BRANCH="${BRANCH:0:20}"
        fi
        # Check for uncommitted changes
        if ! git -C "$CURRENT_DIR" diff --quiet 2>/dev/null || ! git -C "$CURRENT_DIR" diff --cached --quiet 2>/dev/null; then
            GIT_INFO=" ${GREEN}${BRANCH}*${RESET}"
        else
            GIT_INFO=" ${GREEN}${BRANCH}${RESET}"
        fi
    fi
fi

# Color the percentage based on usage
if [ "$PERCENT_USED" -lt 50 ]; then
    PERCENT_COLOR="$GREEN"
elif [ "$PERCENT_USED" -lt 80 ]; then
    PERCENT_COLOR="$YELLOW"
else
    PERCENT_COLOR="$RED"
fi

printf "[${PURPLE}${MODEL}${RESET}] ${BLUE}${CURRENT_DIR##*/}${RESET}${GIT_INFO} ${PERCENT_COLOR}${PERCENT_USED}%%${RESET}\n"
