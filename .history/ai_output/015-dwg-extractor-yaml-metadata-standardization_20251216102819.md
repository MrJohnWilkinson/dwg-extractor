# dwg-extractor YAML Metadata Standardization Plan

## Purpose

Standardize YAML frontmatter across all 28 Claude Code slash commands in dwg-extractor to have consistent `description`, `argument-hint` (where applicable), and `model: opus` in the correct order.

## Target Format

```yaml
---
description: <concise command description>
argument-hint: <argument format hint>
model: opus
<other-metadata>: <e.g., allowed-tools, hints>
---
```

**Order:** description → argument-hint → model → other metadata

## Commands Summary

| Category | Total | Need Updates | Already Compliant |
|----------|-------|--------------|-------------------|
| Top-level | 6 | 2 | 4 |
| dev/ | 11 | 0 | 11 |
| utils/ | 13 | 5 | 8 |
| internal/ | 2 | 0 | 2 |
| **Total** | **32** | **7** | **25** |

## Implementation Details

### Top-Level Commands (6 files)

#### `.claude/commands/breakdown.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/breakdown_to_specs.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/orchestrate-opf.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/orchestrate.md`
**Current:** `model` only
**Action:** Add description, argument-hint
```yaml
---
description: Orchestrate sub-agents to sequentially complete implementation specs
argument-hint: <spec file paths>
model: opus
---
```

#### `.claude/commands/report.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/security-review-full.md`
**Current:** `allowed-tools`, `description` (missing model)
**Action:** Add model, reorder
```yaml
---
description: Complete a security review of the entire codebase
model: opus
allowed-tools: Bash(git ls-files:*), Bash(git status:*), Bash(wc:*), Read, Glob, Grep, LS, Task
---
```

#### `.claude/commands/README.md`
**Action:** Skip (documentation, not a command)

### dev/ Commands (11 files)

All dev/ commands in dwg-extractor already have correct metadata in correct order. No changes needed.

- `.claude/commands/dev/adw-commit.md` ✓
- `.claude/commands/dev/bug.md` ✓
- `.claude/commands/dev/chore.md` ✓
- `.claude/commands/dev/commit.md` ✓
- `.claude/commands/dev/feature.md` ✓
- `.claude/commands/dev/implement.md` ✓
- `.claude/commands/dev/pull_request.md` ✓
- `.claude/commands/dev/test.md` ✓
- `.claude/commands/dev/test_e2e.md` ✓

### utils/ Commands (13 files)

#### `.claude/commands/utils/10-bullet-points.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/archive.md`
**Current:** `model`, `argument-hint` (missing description)
**Action:** Add description, reorder
```yaml
---
description: Archive ai_output and specs directories to tar files
argument-hint: [files to exclude]
model: opus
---
```

#### `.claude/commands/utils/create-alias-ps.md`
**Current:** `model`, `hints`, `argument-hint`, `description` (wrong order)
**Action:** Reorder
```yaml
---
description: Create a new PowerShell alias or function-based alias
argument-hint: [alias_name] [command/path]
model: opus
hints: PowerShell alias creation - $1=alias_name $2=command_or_path
---
```

#### `.claude/commands/utils/create-alias.md`
**Current:** `model`, `hints` only
**Action:** Add description, argument-hint
```yaml
---
description: Create a new bash alias or function-based alias
argument-hint: [alias_name] [command/path]
model: opus
hints: Simple bash alias creation - $1=alias_name $2=command_path
---
```

#### `.claude/commands/utils/find_plan_file.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/install.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/opt-cmd.md`
**Current:** `allowed-tools`, `argument-hint`, `description`, `model` (wrong order)
**Action:** Reorder
```yaml
---
description: Analyze command execution timing using automatic hook-captured timestamps
argument-hint: <path-to-command.md>
model: opus
allowed-tools: Bash(echo:*), Bash(date:*), Bash(find:*), Bash(jq:*), Glob, Read, SlashCommand, AskUserQuestion
---
```

#### `.claude/commands/utils/prepare_app.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/prime.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/start.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/stop.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/tools.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/update_repo_from_template.md`
**Current:** Correct order, complete
**Action:** None required

#### `.claude/commands/utils/update_repo_template.md`
**Current:** `allowed-tools`, `argument-hint`, `description`, `model` (wrong order)
**Action:** Reorder
```yaml
---
description: Sync improved files back to template repository
argument-hint: [PATHS_TO_SYNC]
model: opus
allowed-tools: Bash(git:*), Bash(mkdir:*), Bash(cp:*), Bash(rm:*), Bash(timestamp=*), Bash(TEMP_DIR=*), Bash(ORIG_DIR=*), Bash(cd /tmp/template-sync-*), Bash(for path in*), Bash(done), Bash(if*), Bash(then*), Bash(else*), Bash(fi), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -la* && echo*), Bash(timestamp=$(date +%s) && echo "TIMESTAMP=$timestamp" && echo "TEMP_DIR=/tmp/template-sync-$timestamp" && ls -laR*), Bash(ls:*), Read, Edit(/.claude/commands/*), AskUserQuestion
---
```

### internal/ Commands (2 files)

Both internal/ commands in dwg-extractor already have correct metadata in correct order. No changes needed.

- `.claude/commands/internal/classify_issue.md` ✓
- `.claude/commands/internal/generate_branch_name.md` ✓

## Files Requiring Updates (7 total)

| File | Action |
|------|--------|
| `.claude/commands/orchestrate.md` | Add description, argument-hint |
| `.claude/commands/security-review-full.md` | Add model, reorder |
| `.claude/commands/utils/archive.md` | Add description, reorder |
| `.claude/commands/utils/create-alias-ps.md` | Reorder only |
| `.claude/commands/utils/create-alias.md` | Add description, argument-hint |
| `.claude/commands/utils/opt-cmd.md` | Reorder only |
| `.claude/commands/utils/update_repo_template.md` | Reorder only |

## Validation

After implementation, verify:
1. Run `/utils:prime` - should complete without errors
2. Check CLI shows descriptions: `claude /help` or similar
3. Spot-check a few commands to ensure YAML parses correctly
