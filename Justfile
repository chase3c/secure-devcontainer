# Secure dev container commands

# One command — builds if needed, starts if stopped, shells in
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

# Force rebuild regardless of changes
dc-rebuild:
    #!/usr/bin/env bash
    set -euo pipefail

    devcontainer up --workspace-folder . --remove-existing-container

    HASH=$(find .devcontainer -type f -not -name '.build-hash' -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1)
    echo "$HASH" > .devcontainer/.build-hash

    devcontainer exec --workspace-folder . zsh
