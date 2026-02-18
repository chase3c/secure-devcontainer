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

# GitHub CLI
RUN GH_VERSION=$(curl -fsSL https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/^v//') \
  && ARCH=$(dpkg --print-architecture) \
  && curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${ARCH}.deb" -o /tmp/gh.deb \
  && dpkg -i /tmp/gh.deb \
  && rm /tmp/gh.deb

# GitLab CLI
RUN GLAB_VERSION=$(curl -fsSL https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/releases | jq -r '.[0].tag_name' | sed 's/^v//') \
  && ARCH=$(dpkg --print-architecture) \
  && curl -fsSL "https://gitlab.com/api/v4/projects/gitlab-org%2Fcli/packages/generic/glab/${GLAB_VERSION}/glab_${GLAB_VERSION}_linux_${ARCH}.deb" -o /tmp/glab.deb \
  && dpkg -i /tmp/glab.deb \
  && rm /tmp/glab.deb

# Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get install -y nodejs \
  && rm -rf /var/lib/apt/lists/*

# Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Beans — flat-file issue tracker (https://github.com/hmans/beans)
RUN ARCH=$(dpkg --print-architecture) \
  && case "$ARCH" in amd64) BEANS_ARCH="x86_64";; arm64) BEANS_ARCH="arm64";; *) echo "Unsupported arch: $ARCH" && exit 1;; esac \
  && curl -fsSL "https://github.com/hmans/beans/releases/latest/download/beans_Linux_${BEANS_ARCH}.tar.gz" \
  | tar -xz -C /usr/local/bin beans

# Trust the bind-mounted workspace directory
RUN git config --system --add safe.directory /workspace

# Claude Code config directory (host CLAUDE.md mounted read-only at startup,
# statusline + settings injected by tracking-bridge-setup.py)
RUN mkdir -p /home/$USERNAME/.claude && chown $USERNAME:$USERNAME /home/$USERNAME/.claude

# --- Add your runtime below this line ---
# Examples:
#   Python:   RUN apt-get update && apt-get install -y python3-venv
#   Go:       RUN curl -fsSL https://go.dev/dl/go1.22.0.linux-amd64.tar.gz | tar -C /usr/local -xz
# -----------------------------------------

USER $USERNAME
WORKDIR /workspace

# Dummy tokens — CLIs think they're authenticated, proxy swaps in real credentials.
# gh auth login verifies the token, so write the config file directly.
RUN mkdir -p ~/.config/gh \
  && printf 'github.com:\n    oauth_token: proxy-injected\n    git_protocol: https\n' > ~/.config/gh/hosts.yml
# glab config set doesn't verify, safe to call directly.
RUN glab config set token proxy-injected --host gitlab.com \
  && glab config set git_protocol https --host gitlab.com

SHELL ["/bin/zsh", "-c"]
