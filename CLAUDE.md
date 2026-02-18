# Secure Dev Container Template

## CRITICAL: Security-First Architecture

This repo exists for ONE reason: **isolating AI coding agents from the host system.**

Every design decision prioritizes preventing the agent from accessing, modifying, or exfiltrating host resources. When making changes:

- **NEVER mount host paths as writable** unless there is no alternative. The host filesystem is untrusted territory from the container's perspective — and the container is untrusted territory from the host's perspective.
- **NEVER give the dev user (the agent) access to secrets, keys, or credentials.** Secrets are injected by root-owned processes the dev user cannot read or modify.
- **NEVER add sudo rules** beyond the single `start-proxy.sh` entry. The dev user should not be able to escalate privileges.
- If something doesn't work inside the container (git config, env vars, permissions), fix it **inside the container** using container-local mechanisms (system config, lifecycle scripts). Do NOT open holes back to the host.

## Architecture Summary

- **Credential injection**: mitmproxy running as root injects auth headers into outbound requests. The dev user never sees the real credentials — CLIs are configured with dummy tokens that the proxy replaces on the fly.
- **Secrets file**: Root-owned, mode 600, in `/etc/proxy-secrets/`. Unreadable by the dev user.
- **Host gitconfig**: Bind-mounted read-only. Container sets `safe.directory` via system-level git config (`/etc/gitconfig`), not by writing to the host file.
- **Host CLAUDE.md**: Bind-mounted read-only. Agent sees global instructions but cannot modify them.

## Git

- Do not include "Co-Authored-By" lines in commit messages.
- Push with explicit branch: `git push origin main`.
