# Devcontainer Template

Based on Anthropic Claude Code reference:
https://github.com/anthropics/claude-code/tree/main/.devcontainer

## Primary devcontainer changes required
Start with a copy of these files (copied from the activity-logger repo)
- `.devcontainer/devcontainer.json`
- `.devcontainer/Dockerfile`
- `.devcontainer/init-firewall.sh`
- `.devcontainer/README.md`

These are the only items you MUST update for a new project:

| File | Location | Change From | Change To |
|------|----------|-------------|-----------|
| devcontainer.json | Line 2 | `"name": "activity-logger"` | `"name": "your-project"` |
| devcontainer.json | Line 71 | `npm --prefix app/client install` | Your npm path, or remove if not required |
| init-firewall.sh | Lines 78-79 | `"supabase.co"`, `"supabase.in"` | Your backend domains, or remove if not required |


---

## Secondary devcontainer changes 
Below is the list of all changes that were made to the original Anthropic base devcontainer files, in order to generate a working devcontainer for the acticity logger repo.  
In a new repo, these can be left as they are in many cases.  If the devcontainer is not working as expected in the new repo, the most likely changes required will be to the variables below.  

| File | Component | Anthropic Base | ac-log | Impact |
|------|-----------|----------------|--------|--------|
| devcontainer.json | name | `"Claude Code Sandbox"` | `"activity-logger"` | Cosmetic |
| devcontainer.json | extensions | 4 (base set) | 8 (adds Python, Ruff, Markdown) | Enhanced Python dev |
| devcontainer.json | python.defaultInterpreterPath | Not present | `${workspaceFolder}/.venv/bin/python` | Python venv integration |
| devcontainer.json | mounts (claude config) | `type=volume` (isolated) | `type=bind` (host ~/.claude) | **Config sharing vs isolation** |
| devcontainer.json | mounts (.venv) | Not present | `type=volume` (shadows .venv) | **WSL/container venv isolation** |
| devcontainer.json | containerEnv | 3 vars | 6 vars (adds UV_*, VIRTUAL_ENV, PATH) | Python/uv tooling |
| devcontainer.json | forwardPorts | Not present | `[5173, 8001, 8002]` | App-specific ports |
| devcontainer.json | portsAttributes | Not present | 3 port configs with labels | Port labeling |
| devcontainer.json | postCreateCommand | Not present | uv venv + sync + npm install | Project setup automation |
| Dockerfile | base image | `node:20` | `ubuntu:24.04` | **Different base** |
| Dockerfile | Python | Not present | Manual install (3.12) | Python support |
| Dockerfile | uv package manager | Not present | Installed | Python dependency mgmt |
| Dockerfile | Supabase CLI | Not present | Installed | Database tooling |
| Dockerfile | curl, ca-certificates, wget | Inherited from node:20 | Explicit install | Base image difference |
| Dockerfile | node user creation | Already exists in node:20 | Complex (rename ubuntu) | Base image difference |
| Dockerfile | Node.js | Inherited from node:20 | Manual install via NodeSource | Base image difference |
| init-firewall.sh | Allowed domains | Base domains only | Adds supabase.co, supabase.in | Database connectivity |

---

## ac-log Example 

### devcontainer.json

```json
{
  "name": "activity-logger",
  "build": {
    "dockerfile": "Dockerfile",
    "args": {
      "TZ": "${localEnv:TZ:America/Los_Angeles}",
      "CLAUDE_CODE_VERSION": "latest",
      "GIT_DELTA_VERSION": "0.18.2",
      "ZSH_IN_DOCKER_VERSION": "1.2.0"
    }
  },
  "runArgs": [
    "--cap-add=NET_ADMIN",
    "--cap-add=NET_RAW"
  ],
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "eamodio.gitlens",
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff",
        "shd101wyy.markdown-preview-enhanced"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.codeActionsOnSave": {
          "source.fixAll.eslint": "explicit"
        },
        "terminal.integrated.defaultProfile.linux": "zsh",
        "terminal.integrated.profiles.linux": {
          "bash": {
            "path": "bash",
            "icon": "terminal-bash"
          },
          "zsh": {
            "path": "zsh"
          }
        },
        "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
      }
    }
  },
  "remoteUser": "node",
  "mounts": [
    "source=claude-code-bashhistory-${devcontainerId},target=/commandhistory,type=volume",
    "source=${localEnv:HOME}/.claude,target=/home/node/.claude,type=bind",
    "source=${localWorkspaceFolderBasename}-venv,target=/workspace/.venv,type=volume"
  ],
  "containerEnv": {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/node/.claude",
    "POWERLEVEL9K_DISABLE_GITSTATUS": "true",
    "UV_PROJECT_ENVIRONMENT": "/workspace/.venv",
    "UV_PYTHON_PREFERENCE": "system",
    "VIRTUAL_ENV": "/workspace/.venv",
    "PATH": "/workspace/.venv/bin:/usr/local/share/npm-global/bin:/usr/local/bin:/usr/bin:/bin"
  },
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=delegated",
  "workspaceFolder": "/workspace",
  "forwardPorts": [5173, 8001, 8002],
  "portsAttributes": {
    "5173": { "label": "Vite Frontend", "onAutoForward": "notify" },
    "8001": { "label": "WebSocket Logs", "onAutoForward": "silent" },
    "8002": { "label": "FastAPI Backend", "onAutoForward": "notify" }
  },
  "postStartCommand": "sudo /usr/local/bin/init-firewall.sh",
  "postCreateCommand": "rm -rf /workspace/.venv && uv venv /workspace/.venv --python $(which python3) && uv sync && npm --prefix app/client install",
  "waitFor": "postStartCommand"
}
```

### Dockerfile

```dockerfile
FROM ubuntu:24.04

ARG TZ
ENV TZ="$TZ"

ARG CLAUDE_CODE_VERSION=latest

# Install basic development tools and iptables/ipset
RUN apt-get update && apt-get install -y --no-install-recommends \
  curl \
  ca-certificates \
  wget \
  less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nano \
  vim \
  # Python (3.12 is native on Ubuntu 24.04)
  python3 \
  python3-dev \
  python3-venv \
  python3-pip \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 via NodeSource
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create node user - Ubuntu 24.04 has 'ubuntu' user at UID/GID 1000, rename it to 'node'
RUN if id -u node > /dev/null 2>&1; then \
        echo "node user already exists"; \
    elif id -u ubuntu > /dev/null 2>&1; then \
        echo "Renaming ubuntu -> node"; \
        groupmod -n node ubuntu && \
        usermod -l node -d /home/node -m ubuntu && \
        echo "Renamed successfully"; \
    else \
        echo "Creating node user from scratch"; \
        groupadd --gid 1000 node && \
        useradd --uid 1000 --gid node --shell /bin/bash --create-home node; \
    fi && \
    id node

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Persist bash history.
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/node/.claude && \
  chown -R node:node /workspace /home/node/.claude

WORKDIR /workspace

ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
  mv /root/.local/bin/uv /usr/local/bin/ && \
  mv /root/.local/bin/uvx /usr/local/bin/ || true

# Set up non-root user
USER node

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set the default shell to zsh rather than sh
ENV SHELL=/bin/zsh

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# Default powerline10k theme
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}

# Install Supabase CLI via GitHub releases (npm global install no longer supported)
USER root
RUN ARCH=$(dpkg --print-architecture) && \
    SUPABASE_VERSION=$(curl -s https://api.github.com/repos/supabase/cli/releases/latest | jq -r '.tag_name' | sed 's/^v//') && \
    wget -q "https://github.com/supabase/cli/releases/download/v${SUPABASE_VERSION}/supabase_${SUPABASE_VERSION}_linux_${ARCH}.deb" && \
    dpkg -i "supabase_${SUPABASE_VERSION}_linux_${ARCH}.deb" && \
    rm "supabase_${SUPABASE_VERSION}_linux_${ARCH}.deb"
USER node


# Copy and set up firewall script
COPY init-firewall.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall
USER node
```

### init-firewall.sh

```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, and pipeline failures
IFS=$'\n\t'       # Stricter word splitting

# 1. Extract Docker DNS info BEFORE any flushing
DOCKER_DNS_RULES=$(iptables-save -t nat | grep "127\.0\.0\.11" || true)

# Flush existing rules and delete existing ipsets
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X
ipset destroy allowed-domains 2>/dev/null || true

# 2. Selectively restore ONLY internal Docker DNS resolution
if [ -n "$DOCKER_DNS_RULES" ]; then
    echo "Restoring Docker DNS rules..."
    iptables -t nat -N DOCKER_OUTPUT 2>/dev/null || true
    iptables -t nat -N DOCKER_POSTROUTING 2>/dev/null || true
    echo "$DOCKER_DNS_RULES" | xargs -L 1 iptables -t nat
else
    echo "No Docker DNS rules to restore"
fi

# First allow DNS and localhost before any restrictions
# Allow outbound DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
# Allow inbound DNS responses
iptables -A INPUT -p udp --sport 53 -j ACCEPT
# Allow outbound SSH
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT
# Allow inbound SSH responses
iptables -A INPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
# Allow localhost
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Create ipset with CIDR support
ipset create allowed-domains hash:net

# Fetch GitHub meta information and aggregate + add their IP ranges
echo "Fetching GitHub IP ranges..."
gh_ranges=$(curl -s https://api.github.com/meta)
if [ -z "$gh_ranges" ]; then
    echo "ERROR: Failed to fetch GitHub IP ranges"
    exit 1
fi

if ! echo "$gh_ranges" | jq -e '.web and .api and .git' >/dev/null; then
    echo "ERROR: GitHub API response missing required fields"
    exit 1
fi

echo "Processing GitHub IPs..."
while read -r cidr; do
    if [[ ! "$cidr" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$ ]]; then
        echo "ERROR: Invalid CIDR range from GitHub meta: $cidr"
        exit 1
    fi
    echo "Adding GitHub range $cidr"
    ipset add allowed-domains "$cidr" -exist
done < <(echo "$gh_ranges" | jq -r '(.web + .api + .git)[]' | aggregate -q)

# Resolve and add other allowed domains
for domain in \
    "registry.npmjs.org" \
    "api.anthropic.com" \
    "sentry.io" \
    "statsig.anthropic.com" \
    "statsig.com" \
    "marketplace.visualstudio.com" \
    "vscode.blob.core.windows.net" \
    "update.code.visualstudio.com" \
    "pypi.org" \
    "files.pythonhosted.org" \
    "supabase.co" \
    "supabase.in"; do
    echo "Resolving $domain..."
    ips=$(dig +noall +answer A "$domain" | awk '$4 == "A" {print $5}')
    if [ -z "$ips" ]; then
        echo "WARNING: Failed to resolve $domain, skipping..."
        continue
    fi

    while read -r ip; do
        if [[ ! "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
            echo "ERROR: Invalid IP from DNS for $domain: $ip"
            exit 1
        fi
        echo "Adding $ip for $domain"
        ipset add allowed-domains "$ip" -exist
    done < <(echo "$ips")
done

# Get host IP from default route
HOST_IP=$(ip route | grep default | cut -d" " -f3)
if [ -z "$HOST_IP" ]; then
    echo "ERROR: Failed to detect host IP"
    exit 1
fi

HOST_NETWORK=$(echo "$HOST_IP" | sed "s/\.[0-9]*$/.0\/24/")
echo "Host network detected as: $HOST_NETWORK"

# Set up remaining iptables rules
iptables -A INPUT -s "$HOST_NETWORK" -j ACCEPT
iptables -A OUTPUT -d "$HOST_NETWORK" -j ACCEPT

# Set default policies to DROP first
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# First allow established connections for already approved traffic
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Then allow only specific outbound traffic to allowed domains
iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

# Explicitly REJECT all other outbound traffic for immediate feedback
iptables -A OUTPUT -j REJECT --reject-with icmp-admin-prohibited

echo "Firewall configuration complete"
echo "Verifying firewall rules..."
if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - was able to reach https://example.com"
    exit 1
else
    echo "Firewall verification passed - unable to reach https://example.com as expected"
fi

# Verify GitHub API access
if ! curl --connect-timeout 5 https://api.github.com/zen >/dev/null 2>&1; then
    echo "ERROR: Firewall verification failed - unable to reach https://api.github.com"
    exit 1
else
    echo "Firewall verification passed - able to reach https://api.github.com as expected"
fi
```

---

## Original Anthropic Reference

For comparison, here are the unmodified base files from Anthropic:

### devcontainer.json (base)

```json
{
  "name": "Claude Code Sandbox",
  "build": {
    "dockerfile": "Dockerfile",
    "args": {
      "TZ": "${localEnv:TZ:America/Los_Angeles}",
      "CLAUDE_CODE_VERSION": "latest",
      "GIT_DELTA_VERSION": "0.18.2",
      "ZSH_IN_DOCKER_VERSION": "1.2.0"
    }
  },
  "runArgs": [
    "--cap-add=NET_ADMIN",
    "--cap-add=NET_RAW"
  ],
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "eamodio.gitlens"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.codeActionsOnSave": {
          "source.fixAll.eslint": "explicit"
        },
        "terminal.integrated.defaultProfile.linux": "zsh",
        "terminal.integrated.profiles.linux": {
          "bash": {
            "path": "bash",
            "icon": "terminal-bash"
          },
          "zsh": {
            "path": "zsh"
          }
        }
      }
    }
  },
  "remoteUser": "node",
  "mounts": [
    "source=claude-code-bashhistory-${devcontainerId},target=/commandhistory,type=volume",
    "source=claude-code-config-${devcontainerId},target=/home/node/.claude,type=volume"
  ],
  "containerEnv": {
    "NODE_OPTIONS": "--max-old-space-size=4096",
    "CLAUDE_CONFIG_DIR": "/home/node/.claude",
    "POWERLEVEL9K_DISABLE_GITSTATUS": "true"
  },
  "workspaceMount": "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=delegated",
  "workspaceFolder": "/workspace",
  "postStartCommand": "sudo /usr/local/bin/init-firewall.sh",
  "waitFor": "postStartCommand"
}
```

### Dockerfile (base)

```dockerfile
FROM node:20

ARG TZ
ENV TZ="$TZ"

ARG CLAUDE_CODE_VERSION=latest

# Install basic development tools and iptables/ipset
RUN apt-get update && apt-get install -y --no-install-recommends \
  less \
  git \
  procps \
  sudo \
  fzf \
  zsh \
  man-db \
  unzip \
  gnupg2 \
  gh \
  iptables \
  ipset \
  iproute2 \
  dnsutils \
  aggregate \
  jq \
  nano \
  vim \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ensure default node user has access to /usr/local/share
RUN mkdir -p /usr/local/share/npm-global && \
  chown -R node:node /usr/local/share

ARG USERNAME=node

# Persist bash history.
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  && mkdir /commandhistory \
  && touch /commandhistory/.bash_history \
  && chown -R $USERNAME /commandhistory

# Set `DEVCONTAINER` environment variable to help with orientation
ENV DEVCONTAINER=true

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/node/.claude && \
  chown -R node:node /workspace /home/node/.claude

WORKDIR /workspace

ARG GIT_DELTA_VERSION=0.18.2
RUN ARCH=$(dpkg --print-architecture) && \
  wget "https://github.com/dandavison/delta/releases/download/${GIT_DELTA_VERSION}/git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  sudo dpkg -i "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb" && \
  rm "git-delta_${GIT_DELTA_VERSION}_${ARCH}.deb"

# Set up non-root user
USER node

# Install global packages
ENV NPM_CONFIG_PREFIX=/usr/local/share/npm-global
ENV PATH=$PATH:/usr/local/share/npm-global/bin

# Set the default shell to zsh rather than sh
ENV SHELL=/bin/zsh

# Set the default editor and visual
ENV EDITOR=nano
ENV VISUAL=nano

# Default powerline10k theme
ARG ZSH_IN_DOCKER_VERSION=1.2.0
RUN sh -c "$(wget -O- https://github.com/deluan/zsh-in-docker/releases/download/v${ZSH_IN_DOCKER_VERSION}/zsh-in-docker.sh)" -- \
  -p git \
  -p fzf \
  -a "source /usr/share/doc/fzf/examples/key-bindings.zsh" \
  -a "source /usr/share/doc/fzf/examples/completion.zsh" \
  -a "export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
  -x

# Install Claude
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}


# Copy and set up firewall script
COPY init-firewall.sh /usr/local/bin/
USER root
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && \
  chmod 0440 /etc/sudoers.d/node-firewall
USER node
```

### init-firewall.sh (base)

The base init-firewall.sh is identical to the ac-log version except for the domain list.
Remove these two lines from the domain list if not using Supabase:

```bash
    "supabase.co" \
    "supabase.in"; do
```

Base domains only:

```bash
for domain in \
    "registry.npmjs.org" \
    "api.anthropic.com" \
    "sentry.io" \
    "statsig.anthropic.com" \
    "statsig.com" \
    "marketplace.visualstudio.com" \
    "vscode.blob.core.windows.net" \
    "update.code.visualstudio.com" \
    "pypi.org" \
    "files.pythonhosted.org"; do
```

---

## Optional Removals

### If NOT using Python

Remove from `devcontainer.json`:
- Extensions: `ms-python.python`, `ms-python.vscode-pylance`, `charliermarsh.ruff`
- Setting: `python.defaultInterpreterPath`
- containerEnv: `UV_PROJECT_ENVIRONMENT`, `UV_PYTHON_PREFERENCE`, `VIRTUAL_ENV`
- Update `PATH` to remove `/workspace/.venv/bin:`
- Remove Python parts from `postCreateCommand`

Remove from `Dockerfile`:
- Python packages: `python3`, `python3-dev`, `python3-venv`, `python3-pip`
- uv installation block

### If NOT using Supabase

Remove from `Dockerfile`:
- Supabase CLI installation block (lines 117-124)

Remove from `init-firewall.sh`:
- `"supabase.co"` and `"supabase.in"` from domain list
