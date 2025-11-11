# Claude Code Workflows

This document describes the command workflows available in this project and how they relate to each other.

## Directory Structure

The `.claude/commands/` directory is organized into three subdirectories plus workflow orchestrators at the top level:

### Top Level (Workflow Orchestrators)
Commands that coordinate multi-step workflows and analysis:
- `/report` - Generate analysis reports
- `/breakdown` - Break down large documents into tasks
- `/breakdown_to_specs` - Convert breakdowns into implementation specs
- `/orchestrate` - Coordinate complex multi-command workflows

### `dev/` - Development Workflow
Commands for the core development lifecycle (located in `.claude/commands/dev/`):
- `/dev:feature` - Design and implement new features
- `/dev:bug` - Plan and fix bugs
- `/dev:chore` - Handle maintenance tasks
- `/dev:implement` - Execute implementation plans
- `/dev:test` - Run backend tests
- `/dev:test_e2e` - Run end-to-end tests with Playwright MCP
- `/dev:commit` - Create semantic commits
- `/dev:pull_request` - Generate pull requests with summaries

**Note**: Commands in subdirectories require namespace prefix (e.g., `/dev:feature`), NOT just filename (NOT `/feature`).

### `utils/` - Supporting Tools
Commands for project setup, maintenance, and utilities (located in `.claude/commands/utils/`):
- `/utils:prime` - Understand the codebase (runs git ls-files, reads README)
- `/utils:start` - Start application servers
- `/utils:stop` - Stop running servers
- `/utils:prepare_app` - Prepare application for E2E testing
- `/utils:archive` - Archive completed work
- `/utils:find_plan_file` - Locate implementation plans
- `/utils:install` - Install dependencies
- `/utils:tools` - List available development tools
- `/utils:update_repo_template` - Sync improvements back to template repo

**Note**: Commands in subdirectories require namespace prefix (e.g., `/utils:prime`), NOT just filename (NOT `/prime`).

### `internal/` - ADW Automation
Commands used internally by the AI Developer Workflow system (located in `.claude/commands/internal/`):
- `/internal:classify_issue` - Classify GitHub issues (feature/bug/chore)
- `/internal:generate_branch_name` - Generate semantic branch names

**Note**: Commands in subdirectories require namespace prefix (e.g., `/internal:classify_issue`), NOT just filename (NOT `/classify_issue`).

## Primary Workflows

### 1. Analysis & Planning Workflow

**Goal**: Break down complex requirements into actionable implementation plans

```
/report
  ↓
/breakdown (generates ai_output/XXX-breakdown.md)
  ↓
/breakdown_to_specs (generates specs/XXX-*.md)
  ↓
/orchestrate (coordinates implementation)
```

**When to use:**
- Breaking down large feature requests
- Analyzing complex system changes
- Creating multiple related implementation plans

**Example:**
```bash
# Generate analysis report
/report "Analyze user authentication flow improvements"

# Break down the analysis into tasks
/breakdown ai_output/042-auth-analysis.md

# Convert breakdown into implementation specs
/breakdown_to_specs ai_output/042-auth-breakdown.md

# Orchestrate implementation of all specs
/orchestrate specs/042-*
```

### 2. ADW (AI Developer Workflow)

**Goal**: Automatically process GitHub issues from creation to pull request

```
GitHub Issue Created
  ↓
/internal:classify_issue (determines issue type)
  ↓
/dev:feature | /dev:bug | /dev:chore (creates plan)
  ↓
/dev:implement (executes plan)
  ↓
/dev:test (validates changes)
  ↓
/dev:commit (creates semantic commit)
  ↓
/dev:pull_request (submits for review)
```

**When to use:**
- Automated issue processing with `adws/adw_plan_build.py`
- Consistent workflow for all development tasks
- Ensuring all steps are completed

**Example:**
```bash
# Automatic mode (via ADW script)
cd adws
uv run adw_plan_build.py 123

# Manual mode (step by step)
/internal:classify_issue #123
/dev:feature  # Creates plan
/dev:implement specs/XXX-feature-name.md
/dev:test
/dev:commit
/dev:pull_request
```

### 3. Development Workflow (Manual)

**Goal**: Implement features/fixes without ADW automation

```
/dev:feature | /dev:bug | /dev:chore
  ↓
/dev:implement
  ↓
/dev:test (optional)
  ↓
/dev:commit
  ↓
/dev:pull_request (optional)
```

**When to use:**
- Quick fixes or small changes
- Experimenting with ideas
- Working outside the issue tracking system

**Example:**
```bash
# Plan a new feature
/dev:feature

# Implement the plan
/dev:implement specs/090-my-feature.md

# Run tests
/dev:test

# Commit changes
/dev:commit

# Create PR
/dev:pull_request
```

### 4. Testing Workflow

**Goal**: Validate changes with comprehensive testing

```
/utils:prepare_app (reset to clean state)
  ↓
/utils:start (start servers)
  ↓
/dev:test (backend unit/integration tests)
  ↓
/dev:test_e2e (E2E testing with Playwright MCP)
  ↓
/utils:stop (cleanup)
```

**When to use:**
- Before committing major changes
- Validating E2E user flows
- Regression testing

**Example:**
```bash
# Prepare clean environment
/utils:prepare_app

# Start servers
/utils:start

# Run backend tests
/dev:test

# Run E2E scenarios
/dev:test_e2e

# Stop servers
/utils:stop
```

### 5. Environment Setup Workflow

**Goal**: Get the project running from scratch

```
/utils:install
  ↓
/utils:prime (understand codebase)
  ↓
/utils:start
```

**When to use:**
- First time setup
- After major dependency changes
- Onboarding new developers

**Example:**
```bash
# Install dependencies
/utils:install

# Understand the codebase
/utils:prime

# Start the application
/utils:start
```

### 6. Maintenance Workflow

**Goal**: Keep the project organized and up-to-date

```
/utils:archive (move completed work)
  ↓
/utils:update_repo_template (sync improvements)
```

**When to use:**
- After completing milestones
- Cleaning up old documentation
- Sharing improvements with template repo

**Example:**
```bash
# Archive completed specs
/utils:archive specs/001-*.md

# Sync command improvements back to template
/utils:update_repo_template .claude/commands/dev/feature.md
```

## Workflow Integration

### ADW + Manual Development
Combine automated processing with manual control:

```bash
# ADW processes the issue automatically
cd adws
uv run adw_plan_build.py 123

# Review the generated plan
cat specs/123-feature-name.md

# Make manual adjustments
# ... edit the spec ...

# Re-run implementation with changes
/dev:implement specs/123-feature-name.md
```

### Analysis → ADW Integration
Use analysis workflows to create GitHub issues for ADW:

```bash
# Analyze requirements
/report "User authentication improvements"

# Break down into tasks
/breakdown ai_output/042-auth-analysis.md

# Convert to specs
/breakdown_to_specs ai_output/042-auth-breakdown.md

# Create GitHub issues from specs
gh issue create --title "Implement JWT authentication" --body @specs/042-jwt-auth.md

# Let ADW process each issue
cd adws
uv run trigger_cron.py  # Automatic monitoring
```

### Testing → Development Integration
Incorporate testing into development workflow:

```bash
# Create feature plan
/dev:feature

# Implement with testing
/dev:implement specs/090-my-feature.md
/dev:test
/dev:test_e2e  # If UI changes

# Fix issues found in testing
# ... make fixes ...
/dev:test  # Re-run until passing

# Commit only when tests pass
/dev:commit
```

## Command Selection Guidelines

### When to Use Workflow Orchestrators (Top Level)

Use `/report` when:
- You need structured analysis of a topic
- Generating documentation or summaries
- Creating reference material for future work

Use `/breakdown` when:
- You have a large document to decompose
- Need to create a task list from requirements
- Working with complex multi-step changes

Use `/breakdown_to_specs` when:
- You have a breakdown that needs implementation plans
- Want to create multiple related specs
- Need consistent spec formatting

Use `/orchestrate` when:
- You have multiple related specs to implement
- Want coordinated multi-command execution
- Need to manage complex workflows

### When to Use Development Commands (`dev/`)

Use `/dev:feature` when:
- Adding new functionality
- Extending existing capabilities
- Implementing user-facing changes

Use `/dev:bug` when:
- Fixing reported issues
- Addressing unexpected behavior
- Resolving test failures

Use `/dev:chore` when:
- Refactoring code
- Updating dependencies
- Improving tooling or infrastructure

Use `/dev:implement` when:
- You have a spec ready to execute
- Following a pre-defined plan
- Implementing designs from analysis

Use `/dev:test` when:
- Running backend unit/integration tests
- Validating changes before commit
- Debugging test failures

Use `/dev:test_e2e` when:
- Testing UI interactions
- Validating complete user workflows
- Using Playwright MCP for browser automation

Use `/dev:commit` when:
- Changes are complete and tested
- Ready to create a semantic commit
- Want consistent commit message formatting

Use `/dev:pull_request` when:
- Changes are committed and pushed
- Ready for code review
- Want automated PR description generation

### When to Use Utility Commands (`utils/`)

Use `/utils:prime` when:
- Starting a new session
- Onboarding to the project
- Refreshing understanding of codebase

Use `/utils:start` when:
- Need to run the application
- Testing changes locally
- Running E2E tests

Use `/utils:stop` when:
- Cleaning up after testing
- Freeing ports for other work
- Shutting down development environment

Use `/utils:prepare_app` when:
- Need a clean test environment
- Resetting to known good state
- Before running E2E tests

Use `/utils:archive` when:
- Completed work needs organization
- Cleaning up old documentation
- Preparing for new milestones

Use `/utils:find_plan_file` when:
- Looking for existing specs
- Need to reference past plans
- Searching for implementation details

Use `/utils:install` when:
- First time project setup
- After pulling dependency changes
- Updating development environment

Use `/utils:tools` when:
- Discovering available tooling
- Learning about project capabilities
- Finding the right tool for a task

Use `/utils:update_repo_template` when:
- You improved a command or script
- Want to share improvements upstream
- Maintaining the template repository

### When to Use Internal Commands (`internal/`)

**Note**: These commands are typically used by ADW automation, not manually.

Use `/internal:classify_issue` when:
- ADW needs to determine issue type
- Automating issue processing
- Creating consistent issue categorization

Use `/internal:generate_branch_name` when:
- ADW needs a semantic branch name
- Automating branch creation
- Ensuring naming consistency

## Rationale for 3-Subdirectory Structure

### Why This Structure?

**Problem**: The flat 24-file structure was difficult to navigate and understand:
- No clear grouping of related commands
- Hard to find the right command for a task
- Unclear which commands are for manual use vs automation

**Solution**: Three focused subdirectories:

1. **`dev/`** - Development Lifecycle
   - Clear workflow: plan → implement → test → commit → PR
   - All commands a developer needs for daily work
   - Obvious entry points based on task type

2. **`utils/`** - Supporting Tools
   - Setup and maintenance commands
   - Environment management
   - Helper utilities
   - Not part of core development flow

3. **`internal/`** - ADW Automation
   - Used by automated systems
   - Not typically invoked manually
   - Clearly separated from manual commands

### Benefits

- **Discoverability**: Subdirectory names indicate purpose
- **Mental Model**: Clear separation between development, utilities, and automation
- **Extensibility**: Easy to add new commands to appropriate category
- **Documentation**: Structure is self-documenting
- **Maintainability**: Related commands grouped together

### Design Principles

1. **Purpose-Based Organization**: Commands grouped by what they help you do
2. **Frequency-Based Placement**: Most-used commands (`/dev/*`) have shortest paths
3. **Audience-Based Separation**: Human vs automation commands clearly distinguished
4. **Workflow-Based Grouping**: Commands that work together stay together

## Tips for Effective Workflow Usage

### 1. Start with Understanding
Always begin with `/utils:prime` when starting a new session or picking up work after a break.

### 2. Plan Before Implementing
Use `/dev:feature`, `/dev:bug`, or `/dev:chore` to create a plan before diving into implementation.

### 3. Test Before Committing
Always run `/dev:test` (and `/dev:test_e2e` for UI changes) before creating commits.

### 4. Use ADW for Consistency
When processing GitHub issues, let ADW handle the workflow to ensure all steps are completed.

### 5. Leverage Orchestration
For complex multi-spec changes, use `/orchestrate` to coordinate implementation rather than running commands individually.

### 6. Keep Environment Clean
Use `/utils:stop` to clean up after testing sessions and free resources.

### 7. Document Complex Workflows
When you discover a useful command combination, consider updating this document or creating a custom command.

### 8. Archive Completed Work
Regularly use `/utils:archive` to keep the workspace organized and focused on current work.

## Extending Workflows

### Creating Custom Commands

When creating new commands, place them in the appropriate subdirectory:

- **`dev/`** - If it's part of the core development workflow
- **`utils/`** - If it's a supporting tool or utility
- **`internal/`** - If it's for automation (rare)
- **Top level** - Only if it orchestrates multiple commands

### Modifying Existing Workflows

When improving workflows:
1. Update the command file itself
2. Update this WORKFLOWS.md document
3. Consider syncing to template: `/utils:update_repo_template`

### Creating Workflow Aliases

If you frequently use a command sequence, consider creating a new orchestrator command at the top level that executes the sequence.

## Troubleshooting Workflows

### Commands Not Found After Reorganization
**Solution**: Close and reopen Claude Code to force command rediscovery.

### ADW Not Using New Paths
**Solution**: Check `adws/data_types.py` has updated slash command paths.

### Tab Completion Not Working
**Solution**: Restart Claude Code and verify directory structure matches expected layout.

### Command Execution Fails
**Solution**: Check that file permissions are correct and command file contains valid markdown.

## Resources

- **Command Documentation Standards**: `.claude/commands/README.md`
- **ADW Documentation**: `adws/README.md`
- **Template Infrastructure**: `TEMPLATE_GUIDE.md`
- **Project Documentation**: `README.md`
