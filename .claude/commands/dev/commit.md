# Generate Git Commit (Balanced Style)

Create a detailed conventional commit message with context, changes, and benefits.

## Variables

TYPE: $1 (optional)
DESCRIPTION: $2 (optional)

**Note**: All variables are optional. If not provided, the command will analyze `git diff` to determine an appropriate commit message.

## Instructions

### Commit Message Format

Use the **balanced style** (14-21 lines) with structured sections:

```
<type>: <concise description>

[Context paragraph: 1-2 sentences explaining why this change was needed or what problem it solves]

Changes:
- [Organized bullet describing change 1]
- [Organized bullet describing change 2]
- [Organized bullet describing change 3]

[Optional: Benefits/Results section]
- [Benefit or outcome 1]
- [Benefit or outcome 2]

[Optional: Spec reference if applicable]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Conventional Commit Types

- `feat` - New feature or functionality
- `fix` - Bug fix
- `chore` - Maintenance, refactoring, or non-functional changes
- `test` - Adding or updating tests
- `docs` - Documentation changes
- `refactor` - Code refactoring without changing functionality
- `perf` - Performance improvements
- `ci` - CI/CD pipeline changes

### Subject Line Guidelines

- Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
- 50 characters or less
- Descriptive of the actual changes made
- No period at the end

## Run

### Step 1: Batch Analysis & Metadata Extraction

Run all analysis commands in parallel and extract metadata flags:

1. Run `git status` to see staged/unstaged files
2. Run `git diff --stat` to see file change summary
3. Run `git diff HEAD` to see actual code changes

**Immediately extract metadata:**
- File count: How many files changed?
- Line changes: Total insertions + deletions
- File types: Are they all .md? Mix of code/docs? Test files?
- Spec references: Any files in `specs/` directory?
- Commit type pattern match:
  * `.md` files only → `docs`
  * `tests/`, `*.test.*` files → `test`
  * `.github/workflows/` → `ci`
  * New `app/` files → `feat`
  * Bug fix patterns → `fix`
  * Otherwise → `chore` or `refactor`

**Set format flag:**
- If 1 file changed AND < 50 lines changed → CONCISE format
- Otherwise → BALANCED format

### Step 2: Draft Complete Commit Message (Single Decision Block)

**IMPORTANT:** Draft the COMPLETE commit message during this step. Do not defer any content decisions to Step 3. Step 3 should be pure execution with no analysis.

**Based on Step 1 metadata, draft the complete commit message in ONE analysis:**

**If CONCISE format** (1 file, < 50 lines):
1. Generate: `<type>: <brief description>`
2. Add: 1-sentence explanation (optional)
3. Add: Spec reference if applicable (from Step 1 metadata)
4. Done → Jump to Step 3

**If BALANCED format** (multiple files or > 50 lines):

Pre-compute ALL components at once:

1. **Type**: Already determined in Step 1 metadata
2. **Description**: Concise summary of what changed (50 chars or less)
3. **Context paragraph**: WHY the change was made (1-2 sentences):
   - What problem does this solve?
   - What was the motivation?
   - What was broken or missing?
4. **Changes bullets**: Organize by file/area, use action verbs:
   - Group related changes together
   - Be specific (mention file names, functions, features)
   - Use action verbs (added, updated, removed, fixed, implemented)
   - Keep bullets concise but informative
5. **Benefits section** (if applicable):
   - Performance improvements
   - Better user experience
   - Resolved issues
   - Enabled new capabilities
   - Test results ("162 tests now passing")
6. **Spec reference** (if specs/ files detected in Step 1):
   - Implementing: "Implements: specs/NNN-*.md"
   - Related: "Related to: specs/NNN-*.md"
   - Resolving: "Resolves: specs/NNN-*.md"

Assemble complete message in memory → Ready for Step 3

### Step 3: Execute Git Operations (Chained)

Execute all git operations in a single chained command using the commit message drafted in Step 2:

**Branch safety check:**
- If on `main` or `master` branch → **WARN** user before pushing, ask to confirm
- If on any other branch → proceed with push automatically

```bash
git add -A && git commit -m "$(cat <<'EOF'
<type>: <description>

<context paragraph>

Changes:
- <change 1>
- <change 2>
- <change 3>

<optional benefits section>

<optional spec reference>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)" && git push
```

**If on main/master:**
1. Create commit (without push)
2. Show warning: "⚠️ You are on branch 'main'. Push to main?"
3. Wait for user confirmation
4. If yes: `git push`
5. If no: Stop (commit created but not pushed)

**Result:** Commit created and pushed to current branch (with main/master confirmation)

## Edge Cases

### Trivial Changes
For very trivial changes (typos, minor formatting), you may use a **concise style** without the full structure:
```
<type>: <description>

Brief 1-sentence explanation if needed.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Multiple Concerns
If changes span multiple areas (e.g., frontend + backend + tests), organize bullets by area:
```
Changes:
- Frontend: <changes>
- Backend: <changes>
- Tests: <changes>
```

### No Changes to Commit
If there are no changes staged, report: "No changes to commit"

## Examples

### Example 1: Feature Implementation
```
feat: add dark mode toggle with theme persistence

Added user-configurable dark mode to improve accessibility and reduce eye strain
in low-light environments.

Changes:
- Added theme toggle button in chatbot_page.html with sun/moon icons
- Implemented CSS variables in chatbot_page.css for light/dark themes
- Added localStorage persistence in chatbot_page.js to remember user preference
- Set default theme based on system preference using prefers-color-scheme

Benefits:
- Better accessibility for users in low-light environments
- Reduced eye strain during extended usage
- Seamless theme persistence across sessions

Implements: specs/005-feature-dark-mode-toggle.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Example 2: Bug Fix
```
fix: resolve production deployment VPS permission denied error

Fixed directory ownership preventing Docker image transfers during GitHub Actions
deployment workflow, causing production deployments to fail.

Changes:
- Changed /opt/ai-assistant-production ownership from root:root to ai-assistant:ai-assistant
- Verified nginx configuration permissions remain correct
- Tested successful deployment via workflow run 18933262399

Result: Production deployment now succeeds, all validation tests passing.

Resolves: specs/011-bug-production-deployment-fails-permission-denied.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Example 3: Chore/Refactoring
```
chore: reorganize project structure and archive completed specs

Cleaned up project organization by separating active work from completed/archived
documentation to reduce cognitive load and improve navigation.

Changes:
- Moved completed deployment specs to specs/Archive/
- Archived old planning docs to ai_output/Archive/
- Updated README.md with current project structure
- Added Archive/ to relevant .gitignore patterns

Benefits:
- Clearer separation between active and historical work
- Easier navigation for new contributors
- Reduced clutter in working directories

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Report

After successful execution of Step 3:

1. Display the commit message that was created
2. Show commit hash from git output
3. Confirm whether push was executed (based on branch check)

Format:
```
✅ Commit created: <hash>

<type>: <description>

[rest of commit message]

✅ Pushed to origin/<branch>
```

If any step in the chained operation failed, report the error clearly and indicate which step failed (add, commit, or push).
