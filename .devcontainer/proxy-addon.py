"""
mitmproxy addon that injects real credentials into outbound requests.
This file is owned by root and unreadable by the dev user.

To add a new secret, add a rule to the `request` method below.
"""

import base64
import json

# Secrets are loaded from a root-owned JSON file
SECRETS_FILE = "/etc/proxy-secrets/proxy-secrets.json"


def load_secrets():
    try:
        with open(SECRETS_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _host_matches(host, pattern):
    """Exact match or subdomain match with boundary check.
    e.g. _host_matches("api.cloudflare.com", "api.cloudflare.com") -> True
         _host_matches("api.cloudflare.com.evil.com", "api.cloudflare.com") -> False
    """
    return host == pattern or host.endswith("." + pattern)


class InjectSecrets:
    def __init__(self):
        self.secrets = load_secrets()

    def request(self, flow):
        host = flow.request.pretty_host

        # GitHub — inject personal access token
        # Basic auth works for both API (api.github.com) and git HTTPS (github.com)
        if _host_matches(host, "github.com"):
            token = self.secrets.get("GITHUB_TOKEN")
            if token:
                basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
                flow.request.headers["Authorization"] = f"Basic {basic}"

        # GitLab — inject personal access token
        # Private-Token: for API requests (glab CLI, curl)
        # Basic auth: for git HTTPS operations (push, pull, clone)
        if _host_matches(host, "gitlab.com"):
            token = self.secrets.get("GITLAB_TOKEN")
            if token:
                flow.request.headers["Private-Token"] = token
                basic = base64.b64encode(f"private-token:{token}".encode()).decode()
                flow.request.headers["Authorization"] = f"Basic {basic}"

        # --- Add your rules below ---
        # Example: inject a bearer token for an API
        # if _host_matches(host, "api.example.com"):
        #     token = self.secrets.get("EXAMPLE_API_TOKEN")
        #     if token:
        #         flow.request.headers["Authorization"] = f"Bearer {token}"


addons = [InjectSecrets()]
