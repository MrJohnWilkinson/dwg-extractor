---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(gh:*), Read, Write, AskUserQuestion
argument-hint: [path1] [path2] ...
description: Pull updates from template repository to current project
---

# Update Repository From Template

Pull updates FROM the template repository TO the current project. This command safely syncs specific files from the template repository to your current project, allowing you to selectively adopt template improvements.

## Variables

paths_to_check: $ARGUMENTS (space-separated file and directory paths relative to repo root)

## Instructions

- IMPORTANT: This command pulls template updates INTO current project, never replaces entire project
- IMPORTANT: If no arguments are provided, STOP immediately and alert the user.
- IMPORTANT: Only sync files that are truly template-worthy (commands, docs, configs, scripts)
- NEVER sync project-specific files from template (app code, .env files, data)
- Supports both individual files and directories in arguments
- The template repo is at: `https://github.com/MrJohnWilkinson/claude-code-project-template.git`
- Use shallow clone (`--depth 1`) for faster cloning
- Ask user to confirm changes BEFORE cloning the repository (save time if they want to cancel)
- Use batch copy approach - let git detect changes and file moves automatically
- Check for empty commits before creating them
- Create a descriptive branch name based on what you're pulling
- Show diffs before applying so user can review changes
- Always create a branch (never commit to main directly)
- Clean up temp directory after sync completes or fails

## Workflow

1. **Capture Original Branch**
   - Store the current branch: `ORIGINAL_BRANCH=$(git branch --show-current)`
   - This will be used as the PR base branch later

2. **Validate Input and Preview**
   - Check that all `paths_to_check` exist in current project
   - Verify paths are template-appropriate (not project-specific code)
   - Warn if any paths look project-specific
   - Show preview of paths that will be synced
   - Ask user to confirm: "Proceed with pulling these files from template?"
   - If user rejects, abort immediately (no cleanup needed)

3. **Fast Clone Template Repo**
   - Create temp directory: `/tmp/template-pull-{timestamp}/`
   - Shallow clone: `git clone --depth 1 https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir}`

4. **Create Branch in Current Project**
   - Generate branch name from paths being synced (e.g., `template-sync-commands`)
   - Create and checkout branch: `git checkout -b {branch_name}`

5. **Batch Copy Files from Template**
   - For each path in `paths_to_check`:
     - If directory: Copy entire directory: `cp -r {temp_dir}/{dir_path}/* {dir_path}/`
     - If file: Copy file: `cp {temp_dir}/{file_path} {file_path}`
   - Stage all changes: `git add -A`

6. **Check for Actual Changes**
   - Check if anything was actually modified: `git diff --staged --quiet`
   - If no changes detected:
     - Output: "No changes detected, template files already up to date"
     - Jump to Step 9 (Cleanup)

7. **Show Diff**
   - Display staged changes: `git diff --staged`
   - Output summary: "X files will be updated from template"

8. **Commit, Push, and Create PR**
   - Create descriptive commit message explaining what was pulled
   - Commit changes: `git commit -m "{message}"`
   - Push branch: `git push -u origin {branch_name}`
   - Automatically create PR using gh CLI:
     - Generate title from paths synced: `chore: pull template updates for {short_path_description}`
     - Generate body summarizing what was synced
     - Create PR: `gh pr create --base {ORIGINAL_BRANCH} --title "{title}" --body "{body}"`
   - Output the created PR URL

9. **Cleanup**
   - Return to original project directory
   - Remove temp directory: `rm -rf {temp_dir}`
   - Report success with PR URL
   - Remind user to review and merge PR when ready

## Examples

**Pull updates for single command directory:**
```
/utils:update_repo_from_template .claude/commands/dev
```

**Pull updates for multiple paths:**
```
/utils:update_repo_from_template .claude/commands .mcp.json scripts
```

**Pull updates for specific command file:**
```
/utils:update_repo_from_template .claude/commands/utils/prime.md
```

**Pull updates for configuration and docs:**
```
/utils:update_repo_from_template .mcp.json ai_docs README.md
```

**Pull updates for entire .claude directory:**
```
/utils:update_repo_from_template .claude
```

## Report

- Display summary: "X files updated from template" (or "No changes detected" if no changes)
- List all files that were synced
- Display the created PR URL (from gh pr create output)
- Remind user to review and merge when ready
- Confirm temp directory was cleaned up
