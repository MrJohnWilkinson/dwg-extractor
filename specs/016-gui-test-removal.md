# Chore: GUI Test Removal

## Chore Description
Remove GUI testing infrastructure that was added in spec 015 due to WSL2 X server reliability issues. This cleanup removes test files, dependencies, pytest markers, and associated documentation while preserving the minimal WSL2 limitation note in README. The goal is to revert all GUI testing automation while maintaining the existing core test suite (unit and integration tests).

## Relevant Files
Use these files to resolve the chore:

- **app/tests/gui/** - Directory containing GUI test files (test_widget_structure.py, test_gui_rendering.py, __init__.py) that need to be deleted entirely
- **pyproject.toml** - Project configuration containing:
  - Line 27: pytest-mock dependency in [dependency-groups.dev] that needs removal
  - Lines 35-38: pytest markers configuration (fast, gui) that needs removal
  - Coverage and mypy configurations should remain unchanged
- **README.md** - Project documentation containing:
  - Lines 56-59: GUI test commands that need removal (Run Fast Tests, Run GUI Tests, Run with Coverage variations)
  - Line 61: WSL2 note about `-m fast` that needs removal
  - Line 89: WSL2 GUI limitation note that should be PRESERVED
  - Lines 56, 77, 79: Core test commands that should remain unchanged
- **specs/015-gui-testing-implementation.md** - Spec file that documents the GUI testing implementation (should be deleted or archived)
- **specs/013-test-suite-improvement.md** - Test suite improvement spec that may reference GUI testing in notes (lines 238, 262 mention GUI code exclusion - should remain as context)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Delete GUI test directory
- Remove entire directory `app/tests/gui/` including all files:
  - `app/tests/gui/__init__.py`
  - `app/tests/gui/test_widget_structure.py`
  - `app/tests/gui/test_gui_rendering.py`
  - `app/tests/gui/__pycache__/` (if exists)
- Use `rm -rf app/tests/gui/` command

### Step 2: Remove pytest-mock dependency
- Check if pytest-mock is used anywhere else in codebase with: `grep -r "pytest_mock\|mocker" app/tests/ --include="*.py"`
- If only used for GUI testing, run: `uv remove pytest-mock`
- If used elsewhere, keep the dependency and skip this step
- Verify dependency removed from pyproject.toml [dependency-groups.dev] section

### Step 3: Clean pytest markers from pyproject.toml
- Edit pyproject.toml [tool.pytest.ini_options] section
- Remove lines 35-38 containing the markers configuration:
  ```
  markers = [
      "fast: Fast tests that don't require GUI rendering (introspection only)",
      "gui: GUI rendering tests that require Xvfb display server",
  ]
  ```
- Keep testpaths and pythonpath settings unchanged
- Verify [tool.coverage.run] and [tool.mypy] sections remain untouched

### Step 4: Update README.md Testing section
- Remove lines 57-58 (Run Fast Tests and Run GUI Tests commands)
- Remove line 61 (WSL2 note about `-m fast` marker)
- Update line 56 to simplify: Change "Run complete test suite (unit, integration, GUI)" to "Run complete test suite"
- Remove "including GUI code" phrase from line 59 coverage command description
- PRESERVE line 89: "Skip GUI tests in WSL - X server issues make it unreliable. Focus WSL testing on unit/integration tests only"
- Keep existing commands unchanged:
  - Line 56: `uv run pytest app/tests/`
  - Line 59: `uv run pytest --cov=app app/tests/`
  - Lines 77-80: Working Directory Convention examples

### Step 5: Delete spec 015 GUI testing document
- Remove file: `specs/015-gui-testing-implementation.md`
- This removes the implementation plan for GUI testing infrastructure
- Keep specs/013-test-suite-improvement.md unchanged (it provides context about GUI code exclusion)

### Step 6: Verify no GUI testing references in ai_docs/
- Search ai_docs/ for any GUI testing documentation added during GUI testing work
- Run: `grep -r "GUI test\|xvfb\|pytest.*fast\|pytest.*gui" ai_docs/ --include="*.md"`
- If any files found (other than general mentions), remove GUI testing sections
- Keep ai_docs/001-naming-convention-guide.md unchanged (general testing conventions)

### Step 7: Run validation commands
- Execute all validation commands listed below to ensure:
  - Core tests still pass without GUI testing infrastructure
  - No import errors from removed GUI test files
  - Coverage still works without GUI tests
  - Type checking and linting still pass
  - No broken references to removed markers or commands

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/ -v` - Run core tests to verify no regressions in unit tests
- `uv run pytest app/tests/ -v` - Run all tests (should only run core tests now)
- `uv run pytest --cov=app/core --cov-report=term-missing app/tests/` - Verify coverage still works without GUI tests
- `uv run mypy app/` - Type check all code to ensure no broken imports
- `uv run ruff check app/` - Lint all code to ensure no issues
- `test ! -d app/tests/gui` - Verify GUI test directory is deleted
- `grep -q "pytest-mock" pyproject.toml && echo "FAIL: pytest-mock still present" || echo "PASS: pytest-mock removed"` - Verify pytest-mock removed (if it was GUI-only)
- `grep -q "markers = " pyproject.toml && echo "FAIL: markers still present" || echo "PASS: markers removed"` - Verify pytest markers removed
- `grep -q "xvfb-run" README.md && echo "FAIL: xvfb still in README" || echo "PASS: xvfb removed from README"` - Verify GUI test commands removed from README

## Notes

### Rationale
Per README.md line 89: "Skip GUI tests in WSL - X server issues make it unreliable. Focus WSL testing on unit/integration tests only." The GUI testing infrastructure added in spec 015 proved unreliable in the WSL2 development environment, making it unsuitable for the project's primary development platform.

### What Gets Preserved
- Core test suite (app/tests/core/) remains fully intact
- All existing unit and integration tests continue to work
- Coverage reporting for core modules (extractor.py, excel_writer.py) unchanged
- Type checking and linting configurations unchanged
- One-line WSL2 limitation note in README.md (line 89)
- Spec 013 references to GUI code exclusion (provides historical context)

### What Gets Removed
- All GUI test files and directory structure
- pytest-mock dependency (if only used for GUI mocking)
- pytest markers (fast, gui) from pyproject.toml
- README commands for running GUI tests with markers
- README note about using `-m fast` to skip GUI tests
- Spec 015 document that planned GUI testing implementation

### Testing After Cleanup
After removal, the test suite should:
- Run successfully with `uv run pytest app/tests/`
- Generate coverage reports with `uv run pytest --cov=app/core app/tests/`
- Complete in similar or faster time (no GUI test overhead)
- Pass type checking and linting
- Contain only core module tests (test_extractor.py, test_excel_writer.py)

### Future Considerations
If GUI testing becomes needed in the future:
- Consider alternative approaches that work reliably in WSL2
- Evaluate using mocking exclusively without actual rendering
- Consider running GUI tests only in CI/CD with proper X server
- Document clear platform requirements before implementation
