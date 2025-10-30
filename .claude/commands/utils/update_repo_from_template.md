---
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Read, Write, AskUserQuestion
argument-hint: [path1] [path2] ...
description: Pull updates from template repository to current project
---

# Update Repository From Template

Pull updates FROM the template repository TO the current project. This command safely syncs specific files from the template repository to your current project, allowing you to selectively adopt template improvements.

## Variables

paths_to_check: $ARGUMENTS (space-separated file and directory paths relative to repo root)

## Instructions

- IMPORTANT: This command pulls template updates INTO current project, never replaces entire project
- IMPORTANT: Only sync files that are truly template-worthy (commands, docs, configs, scripts)
- NEVER sync project-specific files from template (app code, .env files, data)
- Supports both individual files and directories in arguments
- Uses basename (filename only) matching to detect RELOCATED files (moved between directories in template)
- Basename matching is SCOPED to argument paths only (prevents false matches outside scope)
- Compares content to detect NEW, UPDATED, RELOCATED, and RELOCATED+UPDATED files
- Skips files with identical content at identical paths to avoid unnecessary operations
- CRITICAL: For RELOCATED files, ALWAYS `git rm` old location before copying to new location (prevents duplicates)
- The template repo is at: `https://github.com/MrJohnWilkinson/claude-code-project-template.git`
- Create a descriptive branch name based on what you're pulling
- Show diffs before applying so user can review changes
- Always create a branch (never commit to main directly)
- Clean up temp directory after sync completes or fails
- IMPORTANT: Always ensure you are in the correct CWD
- IMPORTANT: use tools that will properly find hidden files and folders such as `.claude/commands/`

## Workflow

1. **Validate Input and Categorize**
   - Check that all `paths_to_check` exist in current project
   - Separate arguments into directories vs files
   - Verify paths are template-appropriate (not project-specific code)
   - Warn if any paths look project-specific

2. **Clone Template Repo**
   - Create temp directory: `/tmp/template-pull-{timestamp}/`
   - Clone: `git clone https://github.com/MrJohnWilkinson/claude-code-project-template.git {temp_dir}`

> **CRITICAL - Scoped Basename Detection:**
> This command uses basename (filename only) matching to detect when files have MOVED between directories in the template, BUT only searches within the scope of the argument paths. For example, if you run `/utils:update_repo_from_template .claude/commands` and the template has `.claude/commands/dev/README.md` while your project has `.claude/commands/README.md`, it will detect these as the same file (basename match within scope). However, it will NOT match against `./README.md` in the root because that's outside the `.claude/commands` scope. **This prevents false matches and duplicate files.**

3. **Scan and Compare**
   - For each path in `paths_to_check`:
     - If directory: recursively find all files in that directory (in template repo)
     - If file: check that single file (in template repo)
   - For each file found in template:
     - Extract basename: `basename {template_file_path}`
     - Determine the scope (the top-level argument path containing this file)
     - Search for basename ONLY within that scope in current project: `find {scope_path} -name "{basename}"`
     - If found at DIFFERENT path within scope:
       - Compare content with `cmp -s` or `diff`
       - If IDENTICAL content → Categorize as "RELOCATED" (file exists, just moved to new location in template)
       - If DIFFERENT content → Categorize as "RELOCATED+UPDATED" (file moved AND content changed)
     - If found at SAME path:
       - Compare content
       - If IDENTICAL → Categorize as "SKIP" (already synchronized)
       - If DIFFERENT → Categorize as "UPDATED"
     - If NOT found anywhere in scope → Categorize as "NEW"
   - Build list of NEW, UPDATED, RELOCATED, and RELOCATED+UPDATED files

4. **Present Selection List**
   - Display comprehensive list of all NEW, UPDATED, RELOCATED, and RELOCATED+UPDATED files
   - Format: one file path per line, grouped by category
   - For RELOCATED files, show both current location and new template location
   - Example format:
     ```
     NEW FILES:
     .claude/commands/dev/new_command.md
     scripts/new_utility.sh

     UPDATED FILES:
     .claude/commands/utils/existing_command.md
     .mcp.json

     RELOCATED FILES (template has moved these to new locations):
     .claude/commands/bug.md → .claude/commands/dev/bug.md (identical content)

     RELOCATED+UPDATED FILES (moved AND content changed):
     .claude/commands/chore.md → .claude/commands/dev/chore.md
     ```
   - Instruct user: "Remove any files you DON'T want to pull from template, then paste the edited list back"
   - For RELOCATED files: Explain that adopting them will move the file to the new template structure

5. **User Edits Selection**
   - User removes unwanted file paths from list
   - User pastes back edited list
   - Parse the edited list to get final file selection

6. **Show Diffs**
   - For each selected file:
     - If NEW: show "This file will be created" with full content preview
     - If UPDATED: run `diff` between current and template versions
   - Display all diffs for review

7. **Confirm Changes**
   - Ask user to confirm changes look correct
   - If user rejects, abort and clean up

8. **Create Branch in Current Project**
   - Generate branch name from paths being synced (e.g., `template-sync-commands`)
   - Create and checkout branch: `git checkout -b {branch_name}`

9. **Copy Files from Template**
   - For each selected file:
     - If file is RELOCATED or RELOCATED+UPDATED:
       - CRITICAL: Remove old location first: `git rm {old_path}` (prevents duplicates)
       - Create parent directories for new location: `mkdir -p $(dirname {new_template_path})`
       - Copy from template to new location: `cp {temp_dir}/{new_template_path} {new_template_path}`
     - If file is NEW or UPDATED:
       - Create parent directories if needed: `mkdir -p $(dirname {file_path})`
       - Copy from template to current project: `cp {temp_dir}/{file_path} {file_path}`
   - Stage all changes: `git add -A`
   - IMPORTANT: Always `git rm` old location BEFORE copying to new location for RELOCATED files

10. **Commit and Push**
    - Create descriptive commit message explaining what was pulled from template
    - Commit changes: `git commit -m "{message}"`
    - Push branch: `git push -u origin {branch_name}`
    - Output the branch URL for creating a PR

11. **Cleanup**
    - Return to original project directory
    - Remove temp directory: `rm -rf {temp_dir}`

12. **Report Success**
    - List files that were synced (NEW vs UPDATED counts)
    - Provide current repo branch URL
    - Remind user to create PR or merge branch

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

- Display operation summary: "X new files added, Y files updated, Z files relocated"
- List all files that were synced, grouped by category (NEW, UPDATED, RELOCATED, RELOCATED+UPDATED)
- For RELOCATED files, show old → new path mappings
- Provide the current repo branch URL
- Instruct user to review changes and merge/create PR as needed
- Confirm temp directory was cleaned up
- Confirm no duplicate files were created (old locations removed for relocated files)
