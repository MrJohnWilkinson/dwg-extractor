# Generate Git Commit

Create a conventional commit message based on changes and create the commit.

## Variables (Optional)

type: $1  # Optional: feat, fix, chore, test, docs, refactor, perf
description: $2  # Optional: brief description of changes

**Note**: All variables are optional. If not provided, the command will analyze `git diff` to determine an appropriate commit message.

## Instructions

### Commit Message Format

Use conventional commits standard: `<type>: <description>`

**Types**:
- `feat` - New feature or functionality
- `fix` - Bug fix
- `chore` - Maintenance, refactoring, or non-functional changes
- `test` - Adding or updating tests
- `docs` - Documentation changes
- `refactor` - Code refactoring without changing functionality
- `perf` - Performance improvements

**Description Guidelines**:
- Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
- 50 characters or less
- Descriptive of the actual changes made
- No period at the end

**Examples**:
- `feat: add user authentication module`
- `fix: correct login validation error`
- `chore: update dependencies to latest versions`
- `test: add integration tests for goals`

### Determining Commit Type and Description

**If type and description are provided**: Use them as-is

**If not provided**: Analyze `git diff --stat` to determine:

1. **Determine type** based on file patterns:
   - New features: Look for new files, significant additions in `src/`, `app/`
   - Bug fixes: Look for changes in error handling, validation, fixes in existing code
   - Tests: Changes primarily in `tests/`, `*.test.*`, `*.spec.*` files
   - Docs: Changes in `*.md` files, documentation directories
   - Chore: Changes in config files, dependencies, build scripts

2. **Generate description** from:
   - File names being changed (extract key concepts)
   - Spec file title if implementing a spec
   - Most significant change indicated by git diff

3. **Default to `chore`** if unable to determine type clearly

## Run

1. Run `git diff HEAD` to understand what changes have been made
2. **Determine commit message**:
   - If type provided: Use `<type>: <description>`
   - If not provided: Analyze changes and generate appropriate message
3. Run `git add -A` to stage all changes
4. Run `git commit -m "<generated_commit_message>"`
5. If commit succeeds, report the message
6. If commit fails (e.g., nothing to commit), report the error
7. Push the commits EXCEPT when you are on branch:`main`.  i.e. Push if you are on branch:`ai-assist-stage` but never push if you are on branch:`main`.

## Report

Return the commit message that was used (or error message if commit failed).

**Format**: `<type>: <description>`

**Do NOT include**:
- Agent names or prefixes (keep it conventional commits standard)
- Verbose explanations (just the commit message)
- Additional commentary
