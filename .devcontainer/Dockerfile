FROM debian:bookworm-slim

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

# Non-root user (override UID/GID if needed)
ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID
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

# mitmproxy cert directory (root-owned — dev user never touches private key material)
RUN mkdir -p /etc/mitmproxy-certs && chmod 700 /etc/mitmproxy-certs

# --- Add your runtime below this line ---
# Examples:
#   Node.js:  RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt-get install -y nodejs
#   Python:   RUN apt-get update && apt-get install -y python3-venv
#   Go:       RUN curl -fsSL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | tar -C /usr/local -xz
# -----------------------------------------

USER $USERNAME
WORKDIR /workspace

SHELL ["/bin/zsh", "-c"]
