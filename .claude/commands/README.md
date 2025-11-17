# Claude Code Commands

- All commands must use ONLY the headings listed under `Headings`
- Commands DON'T REQUIRE that ALL headings are used
- Headings should always follow the same order as listed below

## Headings

```
Metadata
# Title (can be renamed, e.g., "# Chore Planning" or "# Bug Planning")
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

## Variables and Arguments

- **Argument-Hint Requires Variables Section** - If `argument-hint` exists in YAML metadata, include `## Variables` section
- **Use ALL_CAPS for Variable Names** - e.g., `DOCUMENT_PATH`, `REPORT_TOPIC`, `BRANCH_NAME`
- **Use Positional Arguments for Fixed Parameters** - Use `$1, $2, $3` for specific, fixed-position parameters
- **Use `$ARGUMENTS` for Variable-Length Inputs** - For inputs that vary in length
- **Map Arguments to Named Variables** - Assign meaningful names (e.g., `BRANCH_NAME: $1`, `PORT_OFFSET: $2`)
- **Document Required vs Optional** - Indicate if required or optional with defaults
- **Use Named Variables in Instructions** - Reference `<BRANCH_NAME>` throughout, NOT `$1`
- **Keep Variable Descriptions Concise** - Brief declarations, not instructional content
- **Follow Standard Heading Order** - Metadata, Title, Purpose, Variables, Instructions, Relevant Files, etc.

## Directory Organization

### Top Level (Workflow Orchestrators)
- `/report` - Generate analysis reports
- `/breakdown` - Break down large documents into tasks
- `/breakdown_to_specs` - Convert breakdowns into implementation specs
- `/orchestrate` - Coordinate complex multi-command workflows
- `README.md`, `WORKFLOWS.md` - Documentation

### `dev/` - Development Workflow
- `/dev:feature`, `/dev:bug`, `/dev:chore` - Plan development tasks
- `/dev:implement` - Execute implementation plans
- `/dev:test`, `/dev:test_e2e` - Run tests
- `/dev:commit`, `/dev:pull_request` - Create commits and PRs

### `utils/` - Supporting Tools
- `/utils:prime` - Understand the codebase
- `/utils:start`, `/utils:stop` - Manage application servers
- `/utils:prepare_app` - Prepare for E2E testing
- `/utils:archive`, `/utils:install`, `/utils:tools` - Maintenance utilities
- `/utils:update_repo_template` - Sync improvements to template repo

### `internal/` - ADW Automation
- `/internal:classify_issue` - Classify GitHub issues
- `/internal:generate_branch_name` - Generate semantic branch names

## Command Invocation

**IMPORTANT**: Commands in subdirectories MUST use namespace prefix (directory:command format).

- ✅ `/dev:feature` (for `.claude/commands/dev/feature.md`)
- ❌ `/feature` (will not be found)
- ✅ `/utils:prime` (for `.claude/commands/utils/prime.md`)
- ✅ `/report` (top-level, no namespace needed)

## Adding New Commands

1. **Choose right subdirectory**: `dev/` (workflow), `utils/` (tools), `internal/` (automation), top-level (orchestrators only)
2. **Follow heading standards** (see above)
3. **Use namespace:filename** - `dev/feature.md` → `/dev:feature`, `report.md` → `/report`
4. **Update documentation** - Add to `WORKFLOWS.md` if part of workflow
5. **Test discovery** - Restart Claude Code after adding commands

## Resources

- **Workflow Documentation**: `WORKFLOWS.md`
- **Template Repository**: https://github.com/MrJohnWilkinson/claude-code-project-template
- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code/slash-commands.md
