---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Read, AskUserQuestion
argument-hint: [file1] [file2] ...
description: Sync improved files back to template repository
---

# Update Repository Template

Update template repository files with improvements made in this project. This command safely syncs specific files from your current project back to the template repository without overwriting the entire template.

## Variables

files_to_sync: $ARGUMENTS (space-separated file paths relative to repo root)

## Instructions

- IMPORTANT: This command ONLY updates specific template files, never the entire project
- IMPORTANT: Only sync files that are truly template-worthy (commands, docs, configs, scripts)
- NEVER sync project-specific files like app code, .env files, or data
- The template repo is at: `https://github.com/MrJohnWilkinson/claude-code-project-template.git`
- Create a descriptive branch name based on what you're updating
- Show diffs before committing so user can review changes
- Always create a branch (never commit to main directly)
- Clean up temp directory after sync completes or fails

## Workflow

1. **Validate Input Files**
   - Check that all `files_to_sync` exist in current project
   - Verify files are template-appropriate (not project-specific code)
   - Warn if any files look project-specific

2. **Clone Template Repo**
   - Create temp directory: `/tmp/template-sync-{timestamp}/`
   - Clone: `git clone https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir}`
   - Change to temp directory

3. **Create Sync Branch**
   - Generate branch name from files being updated (e.g., `update-chore-command`)
   - Create and checkout branch: `git checkout -b {branch_name}`

4. **Copy Files to Template**
   - For each file in `files_to_sync`:
     - Ensure parent directories exist in template repo
     - Copy file from current project to template repo
     - Stage changes: `git add {file}`

5. **Review Changes**
   - Run `git diff --staged` to show what will be committed
   - Ask user to confirm changes look correct
   - If user rejects, abort and clean up

6. **Commit and Push**
   - Create descriptive commit message explaining what was updated
   - Commit changes: `git commit -m "{message}"`
   - Push branch: `git push -u origin {branch_name}`
   - Output the branch URL for creating a PR

7. **Cleanup**
   - Return to original project directory
   - Remove temp directory: `rm -rf {temp_dir}`

8. **Report Success**
   - List files that were synced
   - Provide template repo branch URL
   - Remind user to create PR in template repo

## Examples

**Update single command file:**
```
/utils:update_repo_template .claude/commands/dev/chore.md
```

**Update multiple command files:**
```
/utils:update_repo_template .claude/commands/dev/chore.md .claude/commands/dev/bug.md
```

**Update AI documentation:**
```
/utils:update_repo_template ai_docs/playwright_mcp_setup.md
```

**Update command and related script:**
```
/utils:update_repo_template .claude/commands/dev/install.md scripts/copy_dot_env.sh
```

**Update configuration file:**
```
/utils:update_repo_template .mcp.json
```

## Report

- List all files that were successfully synced to template repo
- Provide the template repo branch URL
- Instruct user to create a PR at: `https://github.com/MrJohnWilkinson/claude-code-project-template/pulls`
- Confirm temp directory was cleaned up
