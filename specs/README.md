# Specifications Directory

Implementation plans for features, bugs, and chores. Used by ADW (AI Developer Workflow) to guide development.

## Purpose

- **Planning documents** - Detailed blueprints for implementation
- **Implementation guides** - Step-by-step instructions for Claude Code
- **Documentation** - Record of design decisions
- **Communication** - Clear requirements and acceptance criteria

## ADW Workflow

1. **GitHub Issue Created** → User creates issue
2. **Classification** → `/classify_issue` determines type (bug/feature/chore)
3. **Planning** → `sdlc_planner` creates spec file
4. **Implementation** → `sdlc_implementor` executes spec
5. **PR Creation** → Changes committed with spec reference

## Unified Spec Template

Create file: `specs/[type]-[description].md`

```markdown
# [Feature/Bug Fix/Chore]: [Title]

## [Feature/Bug/Chore] Description
[1-2 paragraphs describing what needs to be done and why]

## Root Cause (Bug specs only)
[Analysis of what's causing the bug]

## Relevant Files
- `path/to/file.py` - [What changes and why]

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: [First Task]
- [Specific action with file paths and line numbers]
- [Specific action with exact commands]

### Step 2: [Second Task]
- [Specific action]

## Validation Commands
Execute every command to validate completion with zero regressions.

- `command 1` - What this validates
- `uv run --directory app pytest` - All tests pass

## Notes

### Design Decisions
1. **[Decision]**: [Rationale]

### Future Enhancements (optional)
- [Improvement]

### Dependencies (optional)
- [External library needed]
```

## Naming Conventions

- Features: `NNN-feature-name-description.md`
- Bugs: `NNN-fix-bug-description.md`
- Chores: `NNN-chore-task-description.md`

Examples:
- `001-phase1-project-setup.md`
- `002-phase2-core-logic-implementation.md`
- `003-update-readme-files-for-llm.md`

## Writing Effective Specs

1. **Be Specific** - Exact file paths, function names, code snippets
2. **Order Matters** - Number steps that must execute in sequence
3. **Include Validation** - Always provide commands to verify completion
4. **Cover Edge Cases** - Include error handling
5. **Document Decisions** - Explain "why" not just "what"

## Validation Commands

Always include:
- **Test functionality** - Verify feature works
- **Test edge cases** - Cover error scenarios
- **Run tests** - Execute test suite
- **Check regressions** - Ensure nothing broke

Examples:
```bash
uv run --directory app pytest
uv run --directory app pytest --cov=core
test -f path/to/file && echo "File exists"
wc -l README.md
```

## Using Specs

### Manual Implementation
```bash
claude /dev:implement @specs/feature-name.md
```

### ADW Automatic
```bash
# cd adws (removed - use working directory convention)
uv run adw_plan_build.py <issue-number>
```

### Creating Specs
```bash
claude /dev:feature @<issue-url>
claude /dev:bug @<issue-url>
claude /dev:chore @<issue-url>
```

## GitHub Integration

When ADW processes an issue:
1. Issue classified as bug/feature/chore
2. Spec created: `NNN-[type]-[description].md`
3. Implementation follows spec
4. PR references spec
5. Spec remains as documentation

## Common Pitfalls

❌ **Vague**: "Update the code"
✅ **Specific**: "Update `src/api/routes.py:42` to add error handling"

❌ **No Validation**: Missing test commands
✅ **Clear Validation**: "`pytest tests/test_api.py::test_error_handling`"

❌ **Missing Context**: "Fix the bug"
✅ **Detailed**: "Fix NullPointerException in UserService.getUser() when user_id is None"

## Resources

- **ADW Documentation**: `adws/README.md`
- **Slash Commands**: `.claude/commands/README.md`
- **Workflows**: `.claude/commands/WORKFLOWS.md`
