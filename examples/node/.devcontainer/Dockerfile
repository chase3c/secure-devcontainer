# Extends the base secure container with Node.js
FROM debian:bookworm-slim

ARG PNPM_VERSION=10.5.2
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# System essentials + mitmproxy + firewall
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    jq \
    zsh \
    fzf \
    vim-tiny \
    openssh-client \
    ca-certificates \
    sudo \
    iptables \
    python3 \
    python3-pip \
    pipx \
  && rm -rf /var/lib/apt/lists/*

# mitmproxy (runs as root to protect secrets)
RUN pipx install mitmproxy && pipx ensurepath

# Use the built-in node user (uid 1000 already exists in node images)
# Since we're on debian-slim, create it manually
RUN groupadd --gid $USER_GID $USERNAME \
  && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/zsh $USERNAME

# Proxy addon + secrets directory (root-owned, dev user can't read)
RUN mkdir -p /etc/proxy-secrets
COPY proxy-addon.py /etc/proxy-secrets/proxy-addon.py
COPY start-proxy.sh /usr/local/bin/start-proxy.sh
RUN chmod 700 /etc/proxy-secrets \
  && chmod 600 /etc/proxy-secrets/proxy-addon.py \
  && chmod 755 /usr/local/bin/start-proxy.sh

# Sudo: dev user can ONLY run start-proxy.sh as root
RUN echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/bin/start-proxy.sh" > /etc/sudoers.d/$USERNAME \
  && chmod 440 /etc/sudoers.d/$USERNAME

# mitmproxy cert directory (root-owned)
RUN mkdir -p /etc/mitmproxy-certs && chmod 700 /etc/mitmproxy-certs

# --- Node.js runtime ---
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*
RUN corepack enable && corepack prepare pnpm@${PNPM_VERSION} --activate
RUN npm install -g turbo

USER $USERNAME
WORKDIR /workspace

SHELL ["/bin/zsh", "-c"]
