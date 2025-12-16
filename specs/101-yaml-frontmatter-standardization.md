# Chore: Standardize YAML Frontmatter in Claude Code Slash Commands

## Chore Description

Standardize YAML frontmatter across all Claude Code slash commands in the `.claude/commands/` directory to have consistent metadata fields in the correct order: `description` -> `argument-hint` -> `model` -> other metadata (like `allowed-tools`, `hints`). This ensures consistency and proper parsing by Claude Code CLI.

Based on the analysis in `ai_output/015-dwg-extractor-yaml-metadata-standardization.md`, 7 files need updates out of 32 total command files.

## Relevant Files

Use these files to resolve the chore:

- `ai_output/015-dwg-extractor-yaml-metadata-standardization.md` - Contains the full analysis and exact YAML changes needed for each file
- `.claude/commands/orchestrate.md` - Missing description and argument-hint, has only `model: opus`
- `.claude/commands/security-review-full.md` - Has `allowed-tools` and `description` but missing `model`, wrong order
- `.claude/commands/utils/archive.md` - Has `model` and `argument-hint` but missing `description`, wrong order
- `.claude/commands/utils/create-alias-ps.md` - Has all fields but in wrong order (model, hints, argument-hint, description)
- `.claude/commands/utils/create-alias.md` - Missing `description` and `argument-hint`, has only `model` and `hints`
- `.claude/commands/utils/opt-cmd.md` - Has all fields but in wrong order (allowed-tools, argument-hint, description, model)
- `.claude/commands/utils/update_repo_template.md` - Has all fields but in wrong order (allowed-tools, argument-hint, description, model)

## Step by Step Tasks

### Step 1: Update `.claude/commands/orchestrate.md`

- Current YAML:
  ```yaml
  ---
  model: opus
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Orchestrate sub-agents to sequentially complete implementation specs
  argument-hint: <spec file paths>
  model: opus
  ---
  ```

### Step 2: Update `.claude/commands/security-review-full.md`

- Current YAML:
  ```yaml
  ---
  allowed-tools: Bash(git ls-files:*), Bash(git status:*), Bash(wc:*), Read, Glob, Grep, LS, Task
  description: Complete a security review of the entire codebase
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Complete a security review of the entire codebase
  model: opus
  allowed-tools: Bash(git ls-files:*), Bash(git status:*), Bash(wc:*), Read, Glob, Grep, LS, Task
  ---
  ```

### Step 3: Update `.claude/commands/utils/archive.md`

- Current YAML:
  ```yaml
  ---
  model: opus
  argument-hint: [files to exclude]
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Archive ai_output and specs directories to tar files
  argument-hint: [files to exclude]
  model: opus
  ---
  ```

### Step 4: Update `.claude/commands/utils/create-alias-ps.md`

- Current YAML:
  ```yaml
  ---
  model: opus
  hints: PowerShell alias creation - $1=alias_name $2=command_or_path
  argument-hint: [alias_name] [command/path]
  description: Create a new PowerShell alias or function-based alias
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Create a new PowerShell alias or function-based alias
  argument-hint: [alias_name] [command/path]
  model: opus
  hints: PowerShell alias creation - $1=alias_name $2=command_or_path
  ---
  ```

### Step 5: Update `.claude/commands/utils/create-alias.md`

- Current YAML:
  ```yaml
  ---
  model: opus
  hints: Simple bash alias creation - $1=alias_name $2=command_path
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Create a new bash alias or function-based alias
  argument-hint: [alias_name] [command/path]
  model: opus
  hints: Simple bash alias creation - $1=alias_name $2=command_path
  ---
  ```

### Step 6: Update `.claude/commands/utils/opt-cmd.md`

- Current YAML:
  ```yaml
  ---
  allowed-tools: Bash(echo:*), Bash(date:*), Bash(find:*), Bash(jq:*), Glob, Read, SlashCommand, AskUserQuestion
  argument-hint: <path-to-command.md>
  description: Analyze command execution timing using automatic hook-captured timestamps
  model: opus
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Analyze command execution timing using automatic hook-captured timestamps
  argument-hint: <path-to-command.md>
  model: opus
  allowed-tools: Bash(echo:*), Bash(date:*), Bash(find:*), Bash(jq:*), Glob, Read, SlashCommand, AskUserQuestion
  ---
  ```

### Step 7: Update `.claude/commands/utils/update_repo_template.md`

- Current YAML:
  ```yaml
  ---
  allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(timestamp=*), Bash(TEMP_DIR=*), Bash(ORIG_DIR=*), Bash(cd /tmp/template-sync-*), Bash(for path in*), Bash(done), Bash(if*), Bash(then*), Bash(else*), Bash(fi), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -la* && echo*), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -laR*), Bash(ls:*), Read, Edit(/.claude/commands/*), AskUserQuestion
  argument-hint: [PATHS_TO_SYNC]
  description: Sync improved files back to template repository
  model: opus
  ---
  ```
- Update to:
  ```yaml
  ---
  description: Sync improved files back to template repository
  argument-hint: [PATHS_TO_SYNC]
  model: opus
  allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(timestamp=*), Bash(TEMP_DIR=*), Bash(ORIG_DIR=*), Bash(cd /tmp/template-sync-*), Bash(for path in*), Bash(done), Bash(if*), Bash(then*), Bash(else*), Bash(fi), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -la* && echo*), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -laR*), Bash(ls:*), Read, Edit(/.claude/commands/*), AskUserQuestion
  ---
  ```

### Step 8: Validate all YAML frontmatter parses correctly

- Run validation to ensure all 7 updated files have valid YAML frontmatter
- Verify field ordering is consistent: description -> argument-hint -> model -> other metadata

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `head -10 .claude/commands/orchestrate.md` - Verify orchestrate.md has correct YAML frontmatter
- `head -10 .claude/commands/security-review-full.md` - Verify security-review-full.md has correct YAML frontmatter
- `head -10 .claude/commands/utils/archive.md` - Verify archive.md has correct YAML frontmatter
- `head -10 .claude/commands/utils/create-alias-ps.md` - Verify create-alias-ps.md has correct YAML frontmatter
- `head -10 .claude/commands/utils/create-alias.md` - Verify create-alias.md has correct YAML frontmatter
- `head -10 .claude/commands/utils/opt-cmd.md` - Verify opt-cmd.md has correct YAML frontmatter
- `head -10 .claude/commands/utils/update_repo_template.md` - Verify update_repo_template.md has correct YAML frontmatter

## Notes

- The target YAML field order is: `description` -> `argument-hint` (where applicable) -> `model` -> other metadata (`allowed-tools`, `hints`, etc.)
- Not all commands require `argument-hint` - only include it if the command accepts arguments
- The `model: opus` field ensures these commands use the Opus model for execution
- 25 of 32 command files are already compliant and do not need changes
- The `README.md` in `.claude/commands/` is documentation, not a command, and should be skipped
