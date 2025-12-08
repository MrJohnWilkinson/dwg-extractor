# Chore: Create Clean Branch for Content Zone Rebuild

## Chore Description
Create a clean git branch from commit `ad25eab` with retrospective documentation to rebuild the content zone feature without inheriting technical debt from the previous implementation. This involves:
- Preserving current work as a backup tag and reference branch
- Creating a new clean branch from the pre-content-zone commit
- Copying retrospective documentation to the new branch
- Verifying clean working state

## Relevant Files
Use these files to resolve the chore:

- `ai_output/005-content-zone-optimization-retrospective.md` - Lessons learned from previous implementation
- `ai_output/006-rebuild-user-stories-from-e356096.md` - User stories for rebuild
- `ai_output/007-git-rebuild-strategy-analysis.md` - Strategy analysis for clean rebuild
- `ai_output/008-complete-rebuild-user-stories.md` - Complete rebuild requirements

### New Files
None - this is a git-only chore with no code changes.

## Step by Step Tasks

### Step 1: Preserve Current Work
Create backup references for the current implementation:
- Create tag: `git tag backup-content-zone-v1 HEAD`
- Create reference branch: `git branch content-zone-reference dwg-extractor-stage`

### Step 2: Create Clean Rebuild Branch
Create new branch from the pre-content-zone commit:
- `git checkout -b content-zone-rebuild-v2 ad25eab`

### Step 3: Copy Retrospective Documentation from Reference
Copy the 4 retrospective documents from the reference branch:
- `git checkout content-zone-reference -- ai_output/005-content-zone-optimization-retrospective.md`
- `git checkout content-zone-reference -- ai_output/006-rebuild-user-stories-from-e356096.md`
- `git checkout content-zone-reference -- ai_output/007-git-rebuild-strategy-analysis.md`
- `git checkout content-zone-reference -- ai_output/008-complete-rebuild-user-stories.md`

### Step 4: Commit Documentation
Stage and commit the retrospective documents:
- `git add ai_output/`
- Commit with message:
```
docs: add retrospective analysis for content zone rebuild

Include lessons learned from previous implementation attempt.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Step 5: Verify Clean State
Confirm the branch is set up correctly:
- `git status` - should show clean working tree
- `git log --oneline -5` - should show docs commit, then ad25eab

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- Verify git state (no code changes, so no test commands needed):
    - `git log --oneline -3` - verify docs commit followed by ad25eab
    - `ls ai_output/` - verify 4 retrospective documents exist
    - `git status` - verify no uncommitted changes
    - `git tag -l "backup-content-zone-v1"` - verify backup tag exists
    - `git branch -l "content-zone-reference"` - verify reference branch exists

## Notes
- This chore involves NO code changes - only git operations
- Standard test/lint commands are not applicable since no code is modified
- The reference branch `content-zone-reference` can be used during development to:
  - View old implementation: `git show content-zone-reference:app/core/geometry.py`
  - Diff against old implementation: `git diff content-zone-rebuild-v2..content-zone-reference -- app/core/geometry.py`
  - Copy specific files: `git checkout content-zone-reference -- <filepath>`
