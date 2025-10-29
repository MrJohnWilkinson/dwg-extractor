# Claude Code Commands

- All commands must use ONLY the headings options listed under `Headings`.
- `Claude Code Commands` DON'T REQUIRE that ALL headings are used.  eg.  `.claude/commands/dev/bug.md` and `.claude/commands/dev/chore.md` only use SOME of the headings.

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
