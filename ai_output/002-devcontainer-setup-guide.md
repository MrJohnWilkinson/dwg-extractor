# Devcontainer Setup Guide for Claude Code

## Executive Summary

Devcontainers are **local Docker containers** configured via `.devcontainer/devcontainer.json` in each repository. You need one config per repo, but can share a common Dockerfile/docker-compose across projects. The container runs locally via Docker Desktop (not on GitHub), though the same config works with GitHub Codespaces if you want cloud-based development.

## Table Summary

| Question | Answer |
|----------|--------|
| **Where does the container run?** | Locally via Docker Desktop (WSL2 backend) |
| **One config per repo?** | Yes - each repo needs `.devcontainer/devcontainer.json` |
| **Can configs be shared?** | Yes - reference a shared Dockerfile from multiple repos |
| **GitHub involvement?** | Only if using Codespaces (same config works both places) |
| **Network isolation?** | Use firewall rules (not `--network=none`) to allow API calls |
| **Credentials handling** | Pass via `${localEnv:ANTHROPIC_API_KEY}` environment variable |

## Relevant Files

- `.devcontainer/devcontainer.json` - Main configuration file (per repo)
- `.devcontainer/Dockerfile` - Custom container image definition
- `.devcontainer/docker-compose.yml` - Multi-service orchestration (optional)
- `.devcontainer/init-firewall.sh` - Network security hardening script

## How Devcontainers Work

### Architecture on WSL2

```
Windows Host
    ↓
WSL2 (Linux kernel)
    ↓
Docker Desktop (runs in WSL2)
    ↓
Dev Container (isolated Docker container)
    ↓
VS Code (connects via Remote-Containers extension)
```

### Key Points

1. **Containers run locally** - Not on GitHub servers (unless using Codespaces)
2. **VS Code connects remotely** - Your IDE runs on Windows, connects to container
3. **Workspace is mounted** - Your project files are bind-mounted into container
4. **Isolation is real** - Container has its own filesystem, network, processes

## One Config Per Repo (With Sharing)

### Basic Structure (Per Repo)

```
my-project/
└── .devcontainer/
    └── devcontainer.json    # Required per repo
```

### Shared Dockerfile Strategy (Recommended)

```
~/projects/
├── shared-devcontainer/          # Shared config repo
│   ├── Dockerfile                # Common base image
│   ├── docker-compose.yml        # Shared services
│   └── init-firewall.sh          # Security script
│
├── project-a/
│   └── .devcontainer/
│       └── devcontainer.json     # References ../shared-devcontainer/
│
├── project-b/
│   └── .devcontainer/
│       └── devcontainer.json     # Same reference
│
└── project-c/
    └── .devcontainer/
        └── devcontainer.json     # Same reference
```

### Per-Project devcontainer.json (References Shared)

```json
{
  "name": "Project A Development",
  "dockerFile": "../../shared-devcontainer/Dockerfile",
  "context": "../../shared-devcontainer",
  "workspaceFolder": "/workspace",
  "postCreateCommand": "../../shared-devcontainer/init-firewall.sh",
  "remoteEnv": {
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}"
  }
}
```

## Complete Setup Configuration

### Shared Dockerfile

```dockerfile
# shared-devcontainer/Dockerfile
FROM node:20

RUN apt-get update && apt-get install -y \
    git \
    sudo \
    iptables \
    iproute2 \
    fzf \
    zsh \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Configure sudo for firewall
RUN echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall

WORKDIR /workspace
```

### Firewall Script (Security)

```bash
#!/bin/bash
# shared-devcontainer/init-firewall.sh
set -e

# Default-deny policy
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT DROP

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow DNS (required)
sudo iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow SSH (git operations)
sudo iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS (npm, Claude API)
sudo iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

echo "Firewall configured with default-deny policy"
```

### Full devcontainer.json Template

```json
{
  "name": "Claude Code Dev Environment",
  "dockerFile": "Dockerfile",
  "runArgs": ["--cap-add=NET_ADMIN"],
  "features": {
    "ghcr.io/devcontainers/features/git:1": {},
    "ghcr.io/devcontainers/features/github-cli:1": {}
  },
  "postCreateCommand": ".devcontainer/init-firewall.sh",
  "remoteUser": "node",
  "remoteEnv": {
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}"
  },
  "mounts": [
    "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached"
  ],
  "workspaceFolder": "/workspace",
  "customizations": {
    "vscode": {
      "extensions": [
        "anthropic.claude-code",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ],
      "settings": {
        "editor.formatOnSave": true
      }
    }
  }
}
```

## Network Isolation Options

| Approach | Can Install Packages | Can Call Claude API | Data Exfil Risk | Recommended |
|----------|---------------------|---------------------|-----------------|-------------|
| `--network=none` | NO | NO | Very Low | Not viable |
| **Firewall whitelist** | YES | YES | Medium | **Yes** |
| Bridge network (default) | YES | YES | High | No |

**Use firewall rules** - `--network=none` blocks the Claude API, making it useless.

## Credentials Handling

### Set in WSL2 Shell (Before VS Code)

```bash
# Add to ~/.bashrc for persistence
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc

# Then open VS Code
code ~/projects/my-project
```

### Reference in devcontainer.json

```json
{
  "remoteEnv": {
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}"
  }
}
```

### Security Rules

- Never commit `.env` or `.anthropic/` directories
- Use environment variables, not hardcoded files
- Rotate API keys regularly
- Only use `--dangerously-skip-permissions` with trusted repos

## GitHub Codespaces Relationship

| Aspect | Local Devcontainer | GitHub Codespaces |
|--------|-------------------|-------------------|
| **Same config?** | Yes | Yes |
| **Location** | Your machine | GitHub cloud VM |
| **Cost** | Free (your hardware) | Free tier + billing |
| **Startup** | Instant | ~10-30 seconds |

**Same `devcontainer.json` works both places** - no changes needed.

## Quick Start (WSL2)

```bash
# 1. Set API key in WSL
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. Create project structure
mkdir -p ~/projects/my-project/.devcontainer
cd ~/projects/my-project

# 3. Create devcontainer.json (minimal)
cat > .devcontainer/devcontainer.json << 'EOF'
{
  "image": "node:20",
  "postCreateCommand": "npm install -g @anthropic-ai/claude-code",
  "remoteEnv": {
    "ANTHROPIC_API_KEY": "${localEnv:ANTHROPIC_API_KEY}"
  },
  "customizations": {
    "vscode": {
      "extensions": ["anthropic.claude-code"]
    }
  }
}
EOF

# 4. Open in VS Code
code .

# 5. When prompted: "Reopen in Container"
# 6. Inside container terminal:
claude --dangerously-skip-permissions
```

## Recommendations

1. **Create shared-devcontainer repo** - Store common Dockerfile, firewall script, docker-compose
2. **Keep projects in WSL filesystem** - Use `~/projects/`, not `/mnt/c/` (3-10x faster I/O)
3. **Always use firewall script** - Never run without network restrictions
4. **Set credentials in WSL shell** - Use `${localEnv:}` pattern in devcontainer.json
5. **Start minimal, add features** - Use `image` first, add Dockerfile when needed

## Next Steps

1. Create `~/projects/shared-devcontainer/` with Dockerfile and init-firewall.sh
2. Add `.devcontainer/devcontainer.json` to each repo referencing shared config
3. Set `ANTHROPIC_API_KEY` in `~/.bashrc` for persistence
4. Test with a single project before rolling out to all repos
5. Consider GitHub Codespaces for collaborative development

## Sources

- [VS Code: Developing inside a Container](https://code.visualstudio.com/docs/devcontainers/containers)
- [Claude Code: Development Containers](https://docs.claude.com/en/docs/claude-code/devcontainer)
- [Docker Desktop WSL2 Backend](https://docs.docker.com/desktop/features/wsl/)
- [Dev Container Specification](https://containers.dev/implementors/json_reference/)
