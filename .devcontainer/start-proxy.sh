#!/bin/bash
set -euo pipefail
export PATH="/root/.local/bin:$PATH"

SECRETS_DIR="/etc/proxy-secrets"
SECRETS_FILE="$SECRETS_DIR/proxy-secrets.json"
PROXY_ADDON="/etc/proxy-secrets/proxy-addon.py"
CERT_DIR="/etc/mitmproxy-certs"
PUBLIC_CERT="/usr/local/share/ca-certificates/mitmproxy.crt"

# Detect non-root user (first user with uid >= 1000)
DEV_USER=$(getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1; exit}')
DEV_HOME=$(eval echo "~$DEV_USER")

# Ensure secrets file exists
if [ ! -f "$SECRETS_FILE" ]; then
  echo "{}" > "$SECRETS_FILE"
  chmod 600 "$SECRETS_FILE"
  chown root:root "$SECRETS_FILE"
  echo "WARNING: No secrets configured yet."
  echo "Populate ~/.secrets/proxy-secrets.json on the host and rebuild."
fi

# Start mitmproxy in the background as root, listening on port 8080
mitmdump \
  --listen-port 8080 \
  --set confdir="$CERT_DIR" \
  --scripts "$PROXY_ADDON" \
  --quiet &

PROXY_PID=$!

# Wait for proxy to be ready (local port check, no external dependency)
for i in $(seq 1 10); do
  if ss -tln | grep -q ':8080 '; then
    echo "Proxy running on port 8080 (PID $PROXY_PID)"
    break
  fi
  sleep 0.5
done

# Install mitmproxy CA cert into system trust store and for Node.js/Python
if [ -f "$CERT_DIR/mitmproxy-ca-cert.pem" ]; then
  cp "$CERT_DIR/mitmproxy-ca-cert.pem" "$PUBLIC_CERT"
  update-ca-certificates > /dev/null 2>&1
  # Set up trust for common runtimes (idempotent)
  if ! grep -q "NODE_EXTRA_CA_CERTS" "$DEV_HOME/.zshenv" 2>/dev/null; then
    cat >> "$DEV_HOME/.zshenv" <<ENVEOF
export NODE_EXTRA_CA_CERTS=$PUBLIC_CERT
export REQUESTS_CA_BUNDLE=$PUBLIC_CERT
export SSL_CERT_FILE=$PUBLIC_CERT
ENVEOF
    chown "$DEV_USER:$DEV_USER" "$DEV_HOME/.zshenv"
  fi
fi

# Enforce egress — only root (proxy) can reach the internet directly
iptables -F OUTPUT 2>/dev/null || true
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner 0 -j ACCEPT
iptables -A OUTPUT -j DROP
# Block all IPv6 egress (proxy is IPv4 only)
ip6tables -F OUTPUT 2>/dev/null || true
ip6tables -A OUTPUT -o lo -j ACCEPT
ip6tables -A OUTPUT -m owner --uid-owner 0 -j ACCEPT
ip6tables -A OUTPUT -j DROP
echo "Egress firewall active — dev user traffic must go through proxy"

# Fix ownership on any persisted volumes
find "$DEV_HOME" -maxdepth 1 -name ".*_vol" -exec chown -R "$DEV_USER:$DEV_USER" {} \; 2>/dev/null || true
