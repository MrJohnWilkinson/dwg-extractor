---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(gh:*), Read, AskUserQuestion
argument-hint: [file1] [file2] ...
description: Sync improved files back to template repository
---

# Update Repository Template

Update template repository files with improvements made in this project. This command safely syncs specific files from your current project back to the template repository without overwriting the entire template.

## Variables

paths_to_sync: $ARGUMENTS (space-separated file and directory paths relative to repo root)

## Performance Optimizations

- Pre-compute all dynamic values (timestamps, branch names, messages) at workflow start
- Chain sequential bash operations with `&&` to reduce tool calls
- Use parallel tool calls where operations are independent
- Minimize intermediate status outputs during execution

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
   - Single batched bash: Pre-compute workflow variables and validate all paths exist:
     ```bash
     timestamp=$(date +%s) && \
     echo "TIMESTAMP=$timestamp" && \
     echo "TEMP_DIR=/tmp/template-sync-$timestamp" && \
     ls -la {path1} {path2} ... {pathN}
     ```
   - Parse output to extract timestamp value
   - Derive `temp_dir=/tmp/template-sync-{timestamp}` and `branch_name=update-{descriptive}-{timestamp}`
   - IMPORTANT: Do NOT use `test -f` checks before Read - this is redundant (Read will fail if file doesn't exist)
   - Check template-appropriateness: Only read file contents if needed for validation (skip if path is obviously template-worthy like `.claude/commands/**`)
   - Pre-compute commit message, PR title, and PR body based on paths
   - Show preview with pre-computed values
   - Ask user: "Proceed with syncing these files to template repo?"
   - If user rejects, abort immediately (no cleanup needed)

2. **Clone and Setup Branch (Chained)**
   - Single chained operation:
     ```bash
     mkdir -p {temp_dir} && \
     git clone --depth 1 https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir} && \
     cd {temp_dir} && \
     git checkout -b {branch_name}
     ```
   - This eliminates 3 separate tool calls into one
   - Uses pre-computed `temp_dir` and `branch_name` from Step 1

3. **Batch Sync and Stage (Chained)**
   - Chain all copy + stage operations:
     ```bash
     cd {original_dir} && \
     for path in {paths_to_sync}; do
       mkdir -p {temp_dir}/$(dirname $path) && \
       cp -r $path {temp_dir}/$path
     done && \
     cd {temp_dir} && \
     git add -A
     ```
   - Single bash execution instead of N+1 tool calls
   - Preserves source path structure directly in template

4. **Check for Actual Changes**
   - Check if anything was actually modified: `git diff --staged --quiet`
   - If no changes detected:
     - Output: "No changes detected, skipping commit"
     - Jump to Step 6 (Cleanup)

5. **Show Diff**
   - Display staged changes: `git diff --staged`
   - Output summary: "X files will be updated"

6. **Commit, Push, and Create PR (Chained)**
   - Chain all three operations using pre-computed values from Step 1:
     ```bash
     git commit -m "{pre_computed_message}" && \
     git push -u origin {branch_name} && \
     gh pr create --repo MrJohnWilkinson/claude-code-project-template \
       --head {branch_name} --base main \
       --title "{pre_computed_title}" \
       --body "{pre_computed_body}"
     ```
   - Single tool call with all network operations
   - Uses commit message, PR title, and PR body computed in Step 1
   - Output the created PR URL from gh command output

7. **Cleanup**
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

Note:  Just a small change to test timing with a change
