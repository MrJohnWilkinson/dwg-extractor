# Generate Git Commit (Balanced Style)

Create a detailed conventional commit message with context, changes, and benefits.

## Variables (Optional)

type: $1  # Optional: feat, fix, chore, test, docs, refactor, perf
description: $2  # Optional: brief description of changes

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

### Step 1: Analyze Changes

1. Run `git status` to see what files are staged/unstaged
2. Run `git diff --stat` to see file change summary
3. Run `git diff HEAD` to see actual code changes
4. Look for spec files in the changes (specs/*.md)

### Step 2: Determine Commit Components

**Determine type** based on file patterns:
- `feat`: New files in `app/`, new features, new functionality
- `fix`: Bug fixes, error handling changes, fixing broken functionality
- `test`: Changes primarily in `tests/`, `*.test.*`, `*.spec.*` files
- `docs`: Changes in `*.md` files, documentation directories
- `chore`: Config changes, dependency updates, cleanup, refactoring
- `ci`: Changes in `.github/workflows/`
- `refactor`: Code restructuring without functionality changes

**Generate context paragraph**: Explain WHY the change was made:
- What problem does this solve?
- What was the motivation?
- What was broken or missing?

**Organize changes into bullets**:
- Group related changes together
- Be specific about what changed (mention file names, functions, features)
- Use action verbs (added, updated, removed, fixed, implemented)
- Keep bullets concise but informative

**Identify benefits/results** (if applicable):
- Performance improvements
- Better user experience
- Resolved issues
- Enabled new capabilities
- Test results ("162 tests now passing")

**Check for spec references**:
- If changes include files in `specs/` directory
- If implementing a specific spec, use: "Implements: specs/NNN-*.md"
- If related to a spec, use: "Related to: specs/NNN-*.md"
- If resolving a bug spec, use: "Resolves: specs/NNN-*.md"

### Step 3: Create Commit

1. Stage all changes: `git add -A`

2. Create commit using heredoc format for multi-line message:

```bash
git commit -m "$(cat <<'EOF'
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
)"
```

3. Verify commit was created successfully

### Step 4: Push Changes

- Push commits if on `ai-assist-stage` branch
- DO NOT push if on `main` branch
- Use: `git push` (or `git push -u origin <branch>` if needed)

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

After successful commit:
1. Display the commit message that was created
2. Confirm whether push was executed (based on branch)
3. Show commit hash if available

Format:
```
✅ Commit created: <hash>

<type>: <description>

[rest of commit message]

✅ Pushed to origin/<branch>
```

If commit failed, report the error clearly.
