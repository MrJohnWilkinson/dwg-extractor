---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(gh:*), Bash(curl:*), Bash(tar:*)
argument-hint: [PATHS_TO_SYNC]
description: Pull updates from template repository to current project
---

# Update Repository From Template

Pull updates from `https://github.com/MrJohnWilkinson/claude-code-project-template.git` to current project.

## Variables

PATHS_TO_SYNC: $ARGUMENTS (space-separated file/directory paths relative to repo root)

## Instructions

1. Validate PATHS_TO_SYNC provided, check `gh pr list --head template-sync --state open` (abort if exists), delete stale branch if present
2. Fetch & extract: `curl -sL https://github.com/MrJohnWilkinson/claude-code-project-template/archive/refs/heads/main.tar.gz | tar -xz -C /tmp`
3. Create branch `template-sync`, copy each path from `/tmp/claude-code-project-template-main/{path}`, stage all
4. If no changes (`git diff --staged --quiet`), cleanup and exit
5. Show diff, commit with descriptive message, push, create PR: `gh pr create --base {original_branch}`
6. Cleanup: `rm -rf /tmp/claude-code-project-template-main`
