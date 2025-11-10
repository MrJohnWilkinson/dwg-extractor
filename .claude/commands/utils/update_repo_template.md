---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(timestamp=*), Bash(TEMP_DIR=*), Bash(ORIG_DIR=*), Bash(cd /tmp/template-sync-*), Bash(for path in*), Bash(done), Bash(if*), Bash(then*), Bash(else*), Bash(fi), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -la*), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -laR*), Bash(ls:*), Read, Edit(/.claude/commands/*), AskUserQuestion
argument-hint: [file1] [file2] ...
description: Sync improved files back to template repository
---

# Update Repository Template

Update template repository files with improvements made in this project. This command safely syncs specific files from your current project back to the template repository without overwriting the entire template.

## Variables

paths_to_sync: $ARGUMENTS (space-separated file and directory paths relative to repo root)

## Performance Optimizations

- **Front-load all decisions in Step 1** - Pre-compute ALL values (timestamps, commit messages, file lists) before any git operations
- **Chain sequential bash operations** with `&&` to reduce tool calls (validation, clone, copy, commit+push)
- **Combine redundant operations** - Single diff operation serves both validation and display purposes
- **Eliminate AI processing gaps** - Steps 2-6 should execute with zero AI decision-making after Step 1
- **Fix cp nested directory bug** - Use absolute paths and remove existing destinations to prevent duplicate nesting
- Use parallel tool calls where operations are independent
- Target: ~3min execution (down from ~5min baseline) = 40% performance improvement

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
- Show git diff to user before pushing (critical safety check)
- Push directly to main after user confirms diff
- Clean up temp directory after sync completes or fails
- **Optimized workflow: 7 steps total** (reduced from 8 by combining diff operations)

## Workflow

1. **Validate Input and Preview (Front-load All Decisions)**
   - Single batched bash: Pre-compute ALL workflow variables and validate paths exist:
     ```bash
     timestamp=$(date +%s) && \
     echo "TIMESTAMP=$timestamp" && \
     echo "TEMP_DIR=/tmp/template-sync-$timestamp" && \
     ls -la {path1} {path2} ... {pathN} && \
     echo "=== Paths validated ==="
     ```
   - Parse output to extract timestamp value and derive `temp_dir=/tmp/template-sync-{timestamp}`
   - **CRITICAL: Make ALL content decisions during this step** - no analysis should happen after this point:
     * Determine what files are being synced (already visible from ls output)
     * Pre-compute commit message based on paths (e.g., "chore: sync .claude/commands updates to template")
     * Determine if paths are template-appropriate (`.claude/commands/**`, `scripts/`, `.mcp.json`, etc.)
   - IMPORTANT: Do NOT use `test -f` checks before Read - this is redundant (Read will fail if file doesn't exist)
   - Only read file contents if absolutely necessary for validation (skip for obviously template-worthy paths)
   - Show preview with ALL pre-computed values (temp_dir, commit message, file list)
   - Ask user: "Proceed with syncing these files to template repo?"
   - If user rejects, abort immediately (no cleanup needed)
   - **After user confirms, Steps 2-6 should be pure execution with zero AI decision-making**

2. **Clone Template Repo (Chained)**
   - Single chained operation:
     ```bash
     mkdir -p {temp_dir} && \
     git clone --depth 1 https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir}
     ```
   - This eliminates 2 separate tool calls into one
   - Uses pre-computed `temp_dir` from Step 1
   - Clones directly to main branch (no branch creation needed)

3. **Batch Sync and Stage (Chained)**
   - Chain all copy + stage operations:
     ```bash
     ORIG_DIR=$(pwd) && \
     cd {temp_dir} && \
     for path in {paths_to_sync}; do
       rm -rf "$path" && \
       mkdir -p $(dirname "$path") && \
       cp -r "$ORIG_DIR/$path" "$path"
     done && \
     git add -A
     ```
   - Single bash execution instead of N+1 tool calls
   - Removes existing template files first to prevent nested directory issues
   - Uses absolute source paths to avoid cp creating nested structures
   - Preserves source path structure directly in template

4. **Show Diff and Check for Changes (Combined)**
   - Display staged changes: `git diff --staged`
   - Parse diff output to determine if changes exist
   - If diff is empty (no changes detected):
     - Output: "No changes detected, skipping commit"
     - Jump to Step 7 (Cleanup)
   - Otherwise, output summary: "X files will be updated" based on diff stat

5. **User Confirmation**
   - Ask user: "Push these changes to template main?"
   - If user rejects, jump to Step 7 (Cleanup)

6. **Commit and Push (Chained)**
   - Chain commit and push operations using pre-computed commit message from Step 1:
     ```bash
     git commit -m "{pre_computed_message}" && \
     git push origin main
     ```
   - Single tool call with both git operations
   - Pushes directly to main branch
   - Uses commit message computed in Step 1

7. **Cleanup**
   - Remove temp directory: `rm -rf {temp_dir}`
   - Report success with list of synced files
   - Confirm temp directory was cleaned up

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
- Confirm changes were pushed directly to main branch
- Confirm temp directory was cleaned up
