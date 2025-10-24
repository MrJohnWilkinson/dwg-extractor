# Slash Commands - Claude Docs

## Overview

Slash commands control Claude's behavior during interactive sessions. The platform offers built-in commands, custom commands, plugin commands, and MCP slash commands.

## Built-in Slash Commands

| Command | Purpose |
|---------|---------|
| `/add-dir` | Add additional working directories |
| `/agents` | Manage custom AI subagents |
| `/bug` | Report bugs to Anthropic |
| `/clear` | Clear conversation history |
| `/compact [instructions]` | Compact conversation with optional focus |
| `/config` | Open Settings interface |
| `/cost` | Show token usage statistics |
| `/doctor` | Check installation health |
| `/help` | Get usage help |
| `/init` | Initialize project with guide |
| `/login` | Switch Anthropic accounts |
| `/logout` | Sign out |
| `/mcp` | Manage MCP connections |
| `/memory` | Edit memory files |
| `/model` | Select AI model |
| `/permissions` | View/update permissions |
| `/pr_comments` | View pull request comments |
| `/review` | Request code review |
| `/sandbox` | Enable sandboxed bash execution |
| `/rewind` | Rewind conversation/code |
| `/status` | View version and settings |
| `/terminal-setup` | Install key bindings |
| `/usage` | Show plan limits |
| `/vim` | Enter vim mode |

## Custom Slash Commands

### Syntax

```bash
/<command-name> [arguments]
```

### Command Types

**Project Commands**: Stored in `.claude/commands/` directory, shared with team
**Personal Commands**: Stored in `~/.claude/commands/` directory, available across projects

### Features

#### Namespacing

Organize commands in subdirectories. For example, `.claude/commands/frontend/component.md` creates `/component` with "(project:frontend)" designation.

#### Arguments

Use `$ARGUMENTS` to capture all arguments or `$1`, `$2`, etc. for positional parameters.

Example:

```bash
# Command definition
echo 'Fix issue #$ARGUMENTS' > .claude/commands/fix-issue.md

# Usage
/fix-issue 123 high-priority
```

#### Bash Command Execution

Execute bash commands with `!` prefix. Must specify `allowed-tools`:

```yaml
---
allowed-tools: Bash(git add:*), Bash(git status:*)
---

Current git status: !`git status`
```

#### File References

Use `@` prefix to include file contents:

```text
Review the implementation in @src/utils/helpers.js
```

#### Thinking Mode

Commands can trigger extended thinking via extended thinking keywords.

### Frontmatter

Supported frontmatter options:

- `allowed-tools`: Tools the command can use
- `argument-hint`: Expected arguments
- `description`: Brief description
- `model`: Specific model string
- `disable-model-invocation`: Prevent SlashCommand tool execution

## Plugin Commands

Plugin commands integrate seamlessly with Claude Code through plugin marketplaces. They support namespacing with format `/plugin-name:command-name`.

### Structure

Location: `commands/` directory in plugin root
Format: Markdown files with frontmatter

### Invocation Patterns

```bash
/command-name                    # Direct command
/plugin-name:command-name        # Plugin-prefixed
/command-name arg1 arg2         # With arguments
```

## MCP Slash Commands

MCP servers expose prompts as slash commands with dynamic discovery.

### Command Format

```bash
/mcp__<server-name>__<prompt-name> [arguments]
```

### Features

- Automatically available when MCP server is connected
- Support positional and keyword arguments
- Names normalized to underscores

### Managing Connections

Use `/mcp` command to view servers, check status, authenticate with OAuth, and manage tokens.

### Permissions

Wildcards not supported in MCP tool permissions:

- ✅ `mcp__github` (all tools from server)
- ✅ `mcp__github__get_issue` (specific tool)
- ❌ `mcp__github__*` (wildcards unsupported)

## SlashCommand Tool

The `SlashCommand` tool allows Claude to execute custom slash commands programmatically. It only supports:

- User-defined commands
- Commands with `description` frontmatter

### Permission Rules

- **Exact match**: `SlashCommand:/commit`
- **Prefix match**: `SlashCommand:/review-pr:*`

### Character Budget

Default limit: 15,000 characters
Customizable via `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable

### Disabling

```bash
/permissions
# Add to deny rules: SlashCommand
```

## Skills vs Slash Commands

| Aspect | Slash Commands | Agent Skills |
|--------|----------------|--------------|
| Complexity | Simple prompts | Complex capabilities |
| Structure | Single .md file | Directory with resources |
| Discovery | Explicit invocation | Automatic |
| Scope | Project or personal | Project or personal |

**Use slash commands for**: Quick, frequently-used prompts
**Use Skills for**: Comprehensive workflows with multiple steps and files
