# secure-devcontainer

A dev container template for running AI coding agents (Claude Code, Cursor, etc.) with `--dangerously-skip-permissions` without exposing your secrets.

## The problem

AI agents need API keys to do useful work (deploy to Cloudflare, call external APIs, etc.), but giving them raw credentials means a prompt injection could exfiltrate them.

## How this solves it

A local mitmproxy intercepts outbound HTTP requests and injects credentials based on the destination hostname. The agent process never sees the actual tokens.

```
Agent makes API call (no credentials)
  → mitmproxy intercepts
  → Matches destination hostname (strict boundary check)
  → Injects real token from root-owned secrets file
  → Forwards to API
  → Response passes back unchanged
```

### Security layers

| Layer | What it does |
|---|---|
| **Secret isolation** | Secrets in root-owned `/etc/proxy-secrets/` (mode 700). Agent runs as unprivileged user. |
| **Egress firewall** | iptables blocks all direct outbound traffic. Only loopback (to proxy) and root (proxy itself) are allowed. |
| **Strict host matching** | Tokens only injected for exact hostnames. `api.example.com.evil.com` won't match `api.example.com`. |
| **CA key isolation** | mitmproxy certs stored in root-only `/etc/mitmproxy-certs/`. Agent only has the public cert. |
| **Sudo lockdown** | Agent user can only `sudo` the proxy startup script. Nothing else. |

## Quick start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- [Dev Container CLI](https://github.com/devcontainers/cli): `npm install -g @devcontainers/cli`
- [just](https://github.com/casey/just): `brew install just`

### 1. Copy the `.devcontainer/` directory into your project

```bash
cp -r /path/to/secure-devcontainer/.devcontainer /path/to/your-project/
cp /path/to/secure-devcontainer/Justfile /path/to/your-project/
```

### 2. Add your runtime to the Dockerfile

Edit `.devcontainer/Dockerfile` and add your runtime after the marked section. See `examples/` for Node.js and Python examples.

### 3. Create your secrets file

```bash
mkdir -p ~/.secrets
cat > ~/.secrets/proxy-secrets.json << 'EOF'
{
  "EXAMPLE_API_TOKEN": "your-token-here"
}
EOF
```

### 4. Add proxy rules

Edit `.devcontainer/proxy-addon.py` and add rules for your APIs:

```python
if _host_matches(host, "api.example.com"):
    token = self.secrets.get("EXAMPLE_API_TOKEN")
    if token:
        flow.request.headers["Authorization"] = f"Bearer {token}"
```

### 5. Start it

```bash
just dev
```

First run builds the image (takes a few minutes). After that, `just dev` starts instantly and auto-rebuilds if any `.devcontainer/` files change.

### Force rebuild

```bash
just dc-rebuild
```

## How it works

### Traffic flow

All HTTP/HTTPS traffic from the agent user routes through `localhost:8080` (mitmproxy) via `HTTP_PROXY`/`HTTPS_PROXY` env vars. Even if the agent unsets those vars, iptables blocks direct egress at the kernel level.

### Certificate trust

mitmproxy generates a CA cert on first start. The startup script installs it into the system trust store and sets `NODE_EXTRA_CA_CERTS`, `REQUESTS_CA_BUNDLE`, and `SSL_CERT_FILE` so Node.js, Python requests, and other libraries trust the proxy's HTTPS interception.

### File permissions

```
/etc/proxy-secrets/proxy-secrets.json  → root:root 600 (secrets)
/etc/proxy-secrets/proxy-addon.py      → root:root 600 (injection rules)
/etc/mitmproxy-certs/                  → root:root 700 (CA private key)
/usr/local/share/ca-certificates/      → world-readable  (public cert only)
```

## Examples

- **`examples/node/`** — Node.js 22 + pnpm + Turborepo
- **`examples/python/`** — Python 3.12 + uv

Each example has a complete `.devcontainer/` directory you can copy directly into a project.

## Adding the Justfile to your project

If your project already has a `Justfile`, add these recipes:

```just
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    HASH=$(find .devcontainer -type f -not -name '.build-hash' -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1)
    STORED=$(cat .devcontainer/.build-hash 2>/dev/null || echo "")
    if [ "$HASH" != "$STORED" ]; then
        echo "Dev container config changed — rebuilding..."
        devcontainer up --workspace-folder . --remove-existing-container
        echo "$HASH" > .devcontainer/.build-hash
    else
        devcontainer up --workspace-folder .
    fi
    devcontainer exec --workspace-folder . zsh

dc-rebuild:
    #!/usr/bin/env bash
    set -euo pipefail
    devcontainer up --workspace-folder . --remove-existing-container
    HASH=$(find .devcontainer -type f -not -name '.build-hash' -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1)
    echo "$HASH" > .devcontainer/.build-hash
    devcontainer exec --workspace-folder . zsh
```

And add `.devcontainer/.build-hash` to your `.gitignore`.
