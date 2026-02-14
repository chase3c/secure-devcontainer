# Extends the base secure container with Python
FROM debian:bookworm-slim

ARG PYTHON_VERSION=3.12
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
    python3-venv \
    pipx \
  && rm -rf /var/lib/apt/lists/*

# mitmproxy (runs as root to protect secrets)
RUN pipx install mitmproxy && pipx ensurepath

# Non-root user
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

# --- Python runtime ---
# uv for fast package management
RUN pipx install uv

USER $USERNAME
WORKDIR /workspace

SHELL ["/bin/zsh", "-c"]
