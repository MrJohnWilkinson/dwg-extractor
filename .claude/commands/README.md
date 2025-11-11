# Claude Code Commands

- All commands must use ONLY the headings options listed under `Headings`.
- `Claude Code Commands` DON'T REQUIRE that ALL headings are used.  eg.  `.claude/commands/dev/bug.md` and `.claude/commands/dev/chore.md` only use SOME of the headings.
- Headings should always follow the same order as they are listed below.

# Headings

```
Metadata
# Title (The title is the only heading that can be renamed.  eg.  "# Chore Planning" or "# Bug Planning")
## Purpose
## Variables
## Instructions
## Relevant Files
## Codebase Structure
## Workflow
## Expertise
## Template
## Examples
## Report
```

# Using Variables and Arguments in Claude Code Commands

- **Argument-Hint Requires Variables Section** - If `argument-hint` exists in YAML metadata, you MUST include a matching `## Variables` section that documents those arguments.
- **Use ALL_CAPS for Variable Names** - Declared variable names in the Variables section must use ALL_CAPS (e.g., `DOCUMENT_PATH`, `REPORT_TOPIC`, `BRANCH_NAME`).
- **Use Positional Arguments for Fixed Parameters** - Use `$1, $2, $3, ...` when you have specific, fixed-position parameters (e.g., branch name, port number, file type).
- **Use `$ARGUMENTS` for Variable-Length Inputs** - Use `$ARGUMENTS` for inputs that vary in length (e.g., file lists, text blocks, multi-word descriptions).
- **Map Arguments to Named Variables** - In `## Variables`, assign meaningful names to positional arguments (e.g., `BRANCH_NAME: $1`, `PORT_OFFSET: $2`).
- **Document Required vs Optional** - Always indicate if arguments are required or optional with defaults (e.g., `BRANCH_NAME: $1 (required)`, `PORT_OFFSET: $2 (optional, defaults to auto-calculated)`).
- **Use Named Variables in Instructions** - Reference the named variable (e.g., `<BRANCH_NAME>`) throughout instructions, NOT the positional `$1, $2`.
- **Keep Hints Clear with Examples** - Use descriptive hints with examples when helpful (e.g., `argument-hint: [branch-name] [port-offset]`). Avoid vague hints like `<file path>`.
- **Document All Variables** - Include both argument-based AND hardcoded variables in the Variables section (arguments, derived values, and constants).
- **Variables Section for Multiple References** - Use Variables section especially when arguments appear 3+ times in instructions - improves readability.
- **Keep Variable Descriptions Concise** - Variables should be brief declarations, not instructional content. Good: `REPORT_TOPIC: $ARGUMENTS (required)`. Bad: `DOCUMENT_PATH: $ARGUMENTS (required) - File path to the document to break down. This should be a spec, report, or plan file. The breakdown will decompose tasks into work units that can each be completed in a single session.`.
- **Follow Standard Heading Order** - Metadata (YAML frontmatter), # Title, ## Purpose, ## Variables, ## Instructions, ## Relevant Files, (other sections as needed).

## Directory Organization

Commands are organized into subdirectories by purpose:

### Top Level (Workflow Orchestrators)
- `/report` - Generate analysis reports
- `/breakdown` - Break down large documents into tasks
- `/breakdown_to_specs` - Convert breakdowns into implementation specs
- `/orchestrate` - Coordinate complex multi-command workflows
- `README.md` - Command documentation standards (this file)
- `WORKFLOWS.md` - Complete workflow documentation

### `dev/` - Development Workflow
Commands for the core development lifecycle:
- `/dev:feature`, `/dev:bug`, `/dev:chore` - Plan development tasks
- `/dev:implement` - Execute implementation plans
- `/dev:test`, `/dev:test_e2e` - Run tests
- `/dev:commit`, `/dev:pull_request` - Create commits and PRs

### `utils/` - Supporting Tools
Commands for project setup and maintenance:
- `/utils:prime` - Understand the codebase
- `/utils:start`, `/utils:stop` - Manage application servers
- `/utils:prepare_app` - Prepare for E2E testing
- `/utils:archive`, `/utils:install`, `/utils:tools` - Maintenance utilities
- `/utils:update_repo_template` - Sync improvements to template repo

### `internal/` - ADW Automation
Commands used by automated workflows:
- `/internal:classify_issue` - Classify GitHub issues
- `/internal:generate_branch_name` - Generate semantic branch names

## Command Invocation

**IMPORTANT**: Commands in subdirectories MUST be invoked with namespace prefix (directory:command format).

- ✅ Correct: `/dev:feature` (for `.claude/commands/dev/feature.md`)
- ❌ Wrong: `/feature` (will not be found)
- ✅ Correct: `/utils:prime` (for `.claude/commands/utils/prime.md`)
- ✅ Correct: `/report` (for `.claude/commands/report.md` - no namespace needed for top-level)

Subdirectories define the namespace prefix. Top-level commands do not require a namespace prefix.

## Adding New Commands

When creating new commands:

1. **Choose the right subdirectory** based on purpose:
   - `dev/` for development workflow commands
   - `utils/` for supporting tools
   - `internal/` for automation (rare)
   - Top level only for workflow orchestrators

2. **Follow heading standards** (see above)

3. **Use namespace:filename for invocation** - Commands in subdirectories use `namespace:filename` format (e.g., `dev/feature.md` → `/dev:feature`), top-level commands use just `filename` (e.g., `report.md` → `/report`)

4. **Update documentation**:
   - Add to `WORKFLOWS.md` if it's part of a workflow
   - Update this README if it introduces new patterns

5. **Test discovery** - Restart Claude Code after adding new commands

## Resources

- **Workflow Documentation**: See `WORKFLOWS.md` for complete workflow guides and examples
- **Template Repository**: https://github.com/MrJohnWilkinson/claude-code-project-template
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code/slash-commands.md
