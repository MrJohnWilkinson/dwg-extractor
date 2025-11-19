# Chore: Add Ruff Linting to Development Workflow

## Chore Description
Integrate Ruff as a fast Python linter and formatter to improve code quality and enforce consistent code style across the project. This involves:
1. Adding ruff to dev dependencies via uv package manager
2. Configuring ruff in pyproject.toml with appropriate rules, line length, and exclusions compatible with the existing codebase
3. Running ruff check to establish a baseline of current linting issues
4. Reviewing reported issues to identify quick wins vs. breaking changes
5. Selecting a reasonable subset of rules that align with project standards (considering existing mypy strict configuration)
6. Applying auto-fixes for safe, non-breaking changes or manually fixing issues as appropriate

The goal is to enhance the existing quality tooling (pytest, mypy) with modern, fast linting without disrupting the codebase or introducing regressions.

## Relevant Files
Use these files to resolve the chore:

- `pyproject.toml` - Project configuration file where ruff will be added to dev dependencies and configured under `[tool.ruff]` section. Already contains pytest and mypy configuration, so ruff settings should follow similar patterns.
- `app/core/extractor.py` - Core extraction logic that will be linted by ruff. Contains type annotations and docstrings that may trigger linting rules.
- `app/core/excel_writer.py` - Excel generation logic that will be linted. Contains pandas/openpyxl usage that may have import ordering or formatting issues.
- `app/core/constants.py` - Constants definitions that may benefit from ruff's naming convention checks.
- `app/core/logger.py` - Logging setup that will be linted.
- `app/main.py` - GUI entry point that will be linted. Contains customtkinter code that may trigger linting rules.
- `app/tests/core/test_extractor.py` - Unit tests that will be linted. Test code may have different linting requirements.
- `app/tests/core/test_excel_writer.py` - Unit tests for excel writer that will be linted.
- `app/tests/__init__.py` - Test package init files that will be linted.
- `app/core/__init__.py` - Core package init files that will be linted.
- `app/tests/core/__init__.py` - Test core package init files that will be linted.
- `README.md` - Documentation that will be updated to include ruff usage instructions in the Usage section alongside pytest and mypy commands.

### New Files
None - all changes are to existing files.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Install Ruff
- Add ruff to dev dependencies using `uv add --dev ruff`
- Verify installation by running `uv run ruff --version` to confirm ruff is available

### 2. Configure Ruff in pyproject.toml
- Add `[tool.ruff]` section with baseline configuration:
  - Set `line-length = 88` (Black-compatible default, but check if project uses different standard)
  - Set `target-version = "py311"` to match project's Python 3.11+ requirement
  - Add `exclude` patterns: `[".venv", "build", "dist", ".history"]` to match mypy exclusions plus .history directory
- Add `[tool.ruff.lint]` subsection with rule selection:
  - Start with safe, non-controversial rules: `select = ["E", "F", "I"]` where E=pycodestyle errors, F=pyflakes, I=isort (import sorting)
  - Consider adding "W" (pycodestyle warnings), "N" (naming conventions), "UP" (pyupgrade) after baseline check
  - Add `ignore` list for specific rules that conflict with existing code style (populate after baseline check)
- Add `[tool.ruff.lint.isort]` subsection:
  - Configure import sorting to match existing patterns: `known-first-party = ["app", "core"]`
  - Set `force-single-line = false` and `lines-after-imports = 2` for readability
- Add `[tool.ruff.format]` subsection:
  - Set `quote-style = "double"` (check codebase first to match existing style)
  - Set `indent-style = "space"`

### 3. Run Baseline Check
- Execute `uv run ruff check app/` to see all current linting issues across the codebase
- Execute `uv run ruff check app/ --output-format=json > ruff-baseline.json` to capture baseline for comparison (optional, for reporting)
- Review the output to understand:
  - How many issues exist per rule category
  - Which files have the most issues
  - Whether any issues indicate actual bugs vs. style preferences

### 4. Review and Decide on Rules
- Analyze baseline check results to categorize issues:
  - **Auto-fixable safe changes**: Import sorting, whitespace, trailing commas
  - **Manual review needed**: Unused imports/variables that might be intentional, naming convention changes
  - **Breaking or controversial**: Rules that would require significant refactoring
- Make decisions:
  - Keep rules that align with existing mypy strict configuration (type safety, code clarity)
  - Add specific rules to `ignore` list if they conflict with intentional code patterns
  - Document any deferred rules in the Notes section for future consideration

### 5. Apply Fixes
- Run `uv run ruff check app/ --fix` to apply safe auto-fixes (import sorting, whitespace, etc.)
- Review the changes using `git diff` to ensure no unintended modifications
- For any remaining issues that require manual intervention:
  - Fix issues that improve code quality without changing behavior
  - Add `# noqa: <rule>` comments for intentional violations with justification
  - Update `[tool.ruff.lint]` ignore list for project-wide exceptions

### 6. Update Documentation
- Add ruff usage to README.md in the "Usage" section:
  - `uv run ruff check app/` - Check for linting issues
  - `uv run ruff check app/ --fix` - Auto-fix safe issues
  - `uv run ruff format app/` - Format code (if using ruff as formatter)
- Ensure it's listed alongside pytest and mypy for consistency

### 7. Validation
- Run all validation commands to ensure zero regressions
- Verify that ruff check passes (or only shows intentionally ignored issues)
- Confirm tests still pass with 98% coverage
- Verify mypy type checking still passes

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run ruff check app/` - Verify ruff linting passes or only shows documented/intentional violations
- `uv run ruff format app/ --check` - Verify code formatting is consistent (if using ruff formatter)
- `uv run pytest app/tests/` - Verify all tests pass after any code changes from ruff fixes
- `uv run pytest --cov=app/core app/tests/ --cov-report=term-missing` - Verify 98% test coverage maintained
- `uv run mypy app/` - Verify strict type checking still passes after any code modifications

## Notes
- Ruff is significantly faster than pylint/flake8 and can replace multiple tools (isort, pyupgrade, etc.)
- The project already has strict mypy configuration, so focus on complementary linting (style, imports, complexity) rather than overlapping type checks
- Consider starting conservative with rules and expanding over time - better to have clean linting from day one than fighting hundreds of warnings
- Ruff can also be used as a formatter (alternative to Black) via `ruff format`, but this is optional for this chore
- The `.history/` directory should be excluded from linting as it contains file history artifacts
- If any test files have different linting needs (e.g., allow unused fixtures), use per-file overrides: `[tool.ruff.lint.per-file-ignores]`
- Reference: https://docs.astral.sh/ruff/ for full configuration options and rule catalog
