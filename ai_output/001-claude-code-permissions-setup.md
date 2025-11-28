# Claude Code Permissions Setup Guide

## Executive Summary

Claude Code provides multiple approaches to reduce permission prompts, from simple `AllowedTools` configuration to full container isolation. For most developers working on trusted repositories, **configuring `permissions.allow` in `.claude/settings.json`** combined with `defaultMode: "acceptEdits"` provides the best balance of productivity and safety. The `--dangerously-skip-permissions` flag should only be used in isolated Docker/devcontainer environments.

## Table Summary

| Approach | Security | Productivity | Setup Effort | Best For |
|----------|----------|--------------|--------------|----------|
| **AllowedTools in settings.json** | High | High | Low | Daily development on trusted repos |
| **defaultMode: acceptEdits** | High | High | Minimal | Focused coding sessions |
| **Native Sandbox (/sandbox)** | Very High | High | Low | New beta feature - isolated workflows |
| **Docker Devcontainer** | Very High | Maximum | Medium | CI/CD, untrusted code |
| **--dangerously-skip-permissions** | Depends on isolation | Maximum | Requires container | Automation only |
| **Hooks-based Control** | Very High | High | High | Fine-grained dynamic control |

## Relevant Files

- `.claude/settings.json` - Project-level shared settings (checked into git)
- `.claude/settings.local.json` - Personal settings (auto-ignored by git)
- `~/.claude/settings.json` - User global settings
- `/etc/claude-code/managed-settings.json` - Enterprise policies (Linux)

## Recommended Approach: AllowedTools Configuration

The **best option for reuse across your repositories** is a well-configured `.claude/settings.json` with explicit allow rules. This approach:

1. Works immediately without Docker setup
2. Can be templated and copied across repos
3. Balances security with productivity
4. Is version-controlled for team consistency

### Template Configuration for Multi-Repo Use

```json
{
  "defaultMode": "acceptEdits",
  "env": {
    "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": "1"
  },
  "permissions": {
    "allow": [
      "Bash(mkdir:*)",
      "Bash(ls:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(rm:*)",
      "Bash(touch:*)",
      "Bash(chmod:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(find:*)",
      "Bash(tree:*)",
      "Bash(sort:*)",
      "Bash(test:*)",
      "Bash(tar:*)",
      "Bash(git checkout:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git pull:*)",
      "Bash(git fetch:*)",
      "Bash(git branch:*)",
      "Bash(git status:*)",
      "Bash(git diff:*)",
      "Bash(git log:*)",
      "Bash(git stash:*)",
      "Bash(git merge:*)",
      "Bash(git rebase:*)",
      "Bash(git restore:*)",
      "Bash(git mv:*)",
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(yarn:*)",
      "Bash(pnpm:*)",
      "Bash(uv:*)",
      "Bash(pip:*)",
      "Bash(python:*)",
      "Bash(pytest:*)",
      "Bash(bash:*)",
      "Bash(./scripts/*)",
      "Bash(scripts/*)",
      "Write",
      "WebSearch"
    ],
    "deny": [
      "Bash(rm -rf /:*)",
      "Bash(rm -rf /*:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(sudo:*)",
      "Read(.env)",
      "Read(.env.*)",
      "Read(**/*.key)",
      "Read(**/secrets/**)"
    ]
  }
}
```

### Key Permission Patterns

| Pattern | Matches | Example |
|---------|---------|---------|
| `Bash(npm:*)` | Any npm command | `npm install`, `npm run test` |
| `Bash(git commit:*)` | Git commit with any args | `git commit -m "msg"` |
| `Bash(./scripts/*)` | Scripts in ./scripts/ | `./scripts/build.sh` |
| `Read(docs/**)` | All files under docs/ | `docs/api/reference.md` |
| `WebFetch(domain:github.com)` | Specific domain only | `github.com/user/repo` |

## Permission Modes

Set in settings or via CLI flag `--permission-mode`:

| Mode | Behavior |
|------|----------|
| `default` | Prompts for each new tool type |
| `acceptEdits` | Auto-accepts file edits, prompts for bash |
| `plan` | Read-only analysis mode |
| `bypassPermissions` | Skips all prompts (use in containers only) |

## Docker/Devcontainer Setup

For `--dangerously-skip-permissions`, Anthropic recommends isolated containers:

### Quick Devcontainer Setup

1. Create `.devcontainer/devcontainer.json`:
```json
{
  "name": "Claude Code Dev",
  "image": "node:20",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "postCreateCommand": "npm install -g @anthropic-ai/claude-code",
  "runArgs": ["--network=none"]
}
```

2. Open in VS Code → "Reopen in Container"
3. Run: `claude --dangerously-skip-permissions`

### Network Isolation (Critical)

The `--network=none` flag or firewall rules prevent credential exfiltration:

```bash
# init-firewall.sh - whitelist only essential services
iptables -A OUTPUT -d api.anthropic.com -j ACCEPT
iptables -A OUTPUT -d registry.npmjs.org -j ACCEPT
iptables -A OUTPUT -j DROP
```

## Settings File Priority

Settings are merged in this order (highest priority first):

1. **Enterprise managed** - `/etc/claude-code/managed-settings.json` (cannot override)
2. **CLI flags** - `--permission-mode`, `--dangerously-skip-permissions`
3. **Project local** - `.claude/settings.local.json` (personal, gitignored)
4. **Project shared** - `.claude/settings.json` (team settings, in git)
5. **User global** - `~/.claude/settings.json` (personal defaults)

## Your Current Configuration

Your `.claude/settings.json` already has a solid foundation. To maximize productivity:

### Enhancements to Consider

```json
{
  "defaultMode": "acceptEdits",
  "permissions": {
    "allow": [
      // ... existing rules ...
      "Bash(git push:*)",
      "Bash(git pull:*)",
      "Bash(python:*)",
      "Bash(pytest:*)"
    ],
    "deny": [
      // ... existing rules ...
      "Read(.env)",
      "Read(.env.*)"
    ]
  }
}
```

## Recommendations

1. **For immediate productivity gain**: Add `"defaultMode": "acceptEdits"` to your settings.json - this alone eliminates most file edit prompts

2. **For cross-repo reuse**: Create a template settings.json with common patterns, copy to each repo's `.claude/` directory

3. **For CI/CD automation**: Use Docker devcontainer with network isolation + `--dangerously-skip-permissions`

4. **For maximum security**: Keep using hooks for dynamic validation, add explicit deny rules for sensitive files

5. **Avoid `--dangerously-skip-permissions` on host**: Only use inside containers with network isolation

## Next Steps

1. Add `"defaultMode": "acceptEdits"` to `.claude/settings.json` for immediate improvement
2. Create a template settings.json in your dotfiles repo for reuse
3. Consider setting up a devcontainer for automated workflows
4. Test the new `/sandbox` beta feature when available for native isolation

## Sources

- [Claude Code Settings Documentation](https://docs.anthropic.com/en/docs/claude-code/settings)
- [Claude Code Security Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Claude Code Sandboxing Announcement](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Devcontainer Setup Guide](https://docs.anthropic.com/en/docs/claude-code/devcontainer)
