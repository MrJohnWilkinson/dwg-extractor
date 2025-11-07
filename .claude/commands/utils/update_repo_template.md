---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(gh:*), Read, AskUserQuestion
argument-hint: [file1] [file2] ...
description: Sync improved files back to template repository
---

# Update Repository Template

Update template repository files with improvements made in this project. This command safely syncs specific files from your current project back to the template repository without overwriting the entire template.

## Variables

paths_to_sync: $ARGUMENTS (space-separated file and directory paths relative to repo root)

## Instructions

- IMPORTANT: This command ONLY updates specific template files, never the entire project.  
- IMPORTANT: If no arguments are provided.  STOP immediately and alert the user.
- IMPORTANT: Only sync files that are truly template-worthy (commands, docs, configs, scripts)
- NEVER sync project-specific files like app code, .env files, or data
- Supports both individual files and directories in arguments
- The template repo is at: `https://github.com/MrJohnWilkinson/claude-code-project-template.git`
- Use shallow clone (`--depth 1`) for faster cloning
- Ask user to confirm changes BEFORE cloning the repository (save time if they want to cancel)
- Use batch sync approach - let git detect changes and duplicates
- Check for empty commits before creating them
- Create a descriptive branch name based on what you're updating
- Show diffs before committing so user can review changes
- Always create a branch (never commit to main directly)
- Clean up temp directory after sync completes or fails

## Workflow

1. **Validate Input and Preview**
   - Check that all `paths_to_sync` exist in current project
   - Separate arguments into directories vs files
   - Verify paths are template-appropriate (not project-specific code)
   - Warn if any paths look project-specific
   - Show preview of files that will be synced
   - Ask user to confirm: "Proceed with syncing these files to template repo?"
   - If user rejects, abort immediately (no cleanup needed)

2. **Fast Clone Template Repo**
   - Create temp directory: `/tmp/template-sync-{timestamp}/`
   - Shallow clone: `git clone --depth 1 https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir}`
   - Change to temp directory

3. **Create Sync Branch**
   - Generate branch name from files being updated (e.g., `update-chore-command`)
   - Create and checkout branch: `git checkout -b {branch_name}`

4. **Batch Sync Files**
   - Build file lookup once: `find . -type f > /tmp/template-files.txt`
   - For each file in `paths_to_sync`:
     - Find target in template: `grep "$(basename $file)" /tmp/template-files.txt | head -1`
     - Create parent directory if needed: `mkdir -p $(dirname $target)`
     - Copy file: `cp $file $target`
   - For each directory in `paths_to_sync`:
     - Copy entire directory: `cp -r $dir $target_dir`
   - Stage all changes: `git add -A`

5. **Check for Actual Changes**
   - Check if anything was actually modified: `git diff --staged --quiet`
   - If no changes detected:
     - Output: "No changes detected, skipping commit"
     - Jump to Step 8 (Cleanup)

6. **Show Diff**
   - Display staged changes: `git diff --staged`
   - Output summary: "X files will be updated"

7. **Commit, Push, and Create PR**
   - Create descriptive commit message explaining what was updated
   - Commit changes: `git commit -m "{message}"`
   - Push branch: `git push -u origin {branch_name}`
   - Automatically create PR in template repo using gh CLI:
     - Generate title from paths synced: `chore: update template with {short_path_description}`
     - Generate body summarizing what was synced from current project
     - Create PR: `gh pr create --base main --title "{title}" --body "{body}"`
     - Note: Base branch is always `main` since we're pushing to the template repo
   - Output the created PR URL

8. **Cleanup**
   - Return to original project directory
   - Remove temp directory: `rm -rf {temp_dir}`
   - Report success with PR URL
   - Remind user to review and merge PR in template repo when ready

## Examples

**Update single command file:**
```
/utils:update_repo_template .claude/commands/dev/chore.md
```

**Update multiple command files:**
```
/utils:update_repo_template .claude/commands/dev/chore.md .claude/commands/dev/bug.md
```

**Restructure with directories and files (namespace migration):**
```
/utils:update_repo_template .claude/commands/dev .claude/commands/dev/bug.md .claude/commands/dev/chore.md .claude/commands/internal .claude/commands/internal/classify_issue.md .claude/commands/README.md
```

**Update entire directory tree:**
```
/utils:update_repo_template .claude/commands/dev .claude/commands/utils .claude/commands/internal
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

- Display summary: "X files updated" (or "No changes detected" if no changes)
- List all files that were synced
- Display the created PR URL in template repo (from gh pr create output)
- Remind user to review and merge PR in template repo when ready
- Confirm temp directory was cleaned up
