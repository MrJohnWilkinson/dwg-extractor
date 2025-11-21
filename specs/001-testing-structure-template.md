# Chore: Create Testing Structure and Organisation Template

## Chore Description
Review the codebase testing structure and organisation to create a reusable template document that describes good testing practices, file organisation, test patterns, and fixture management. This template can be used in other projects to establish consistent, maintainable test suites.

## Relevant Files
Use these files to resolve the chore:

- `README.md` - Contains the project's testing commands and conventions
- `pyproject.toml` - Contains pytest configuration, coverage settings, and test path configuration
- `app/tests/` - Contains the test suite structure to analyse
- `app/tests/core/test_extractor.py` - Comprehensive unit tests demonstrating test patterns
- `app/tests/core/test_geometry.py` - Focused module tests with parametrized cases
- `app/tests/core/test_excel_formatting.py` - Tests with fixtures and complex assertions
- `app/tests/core/test_excel_writer.py` - Integration tests with temp directories
- `app/tests/assets/` - Test fixture files (DXF files and generator scripts)
- `app/core/constants.py` - Application constants used in tests

### New Files
- `ai_docs/010-testing-structure-template.md` - The output template document

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyse Current Test Structure
- Review the directory layout: `app/tests/` with `core/` subdirectory mirroring `app/core/`
- Document the file naming convention: `test_<module_name>.py`
- Note the `__init__.py` files in test directories for package discovery
- Identify that tests are co-located under `app/tests/` rather than at project root

### Step 2: Document Working Directory Convention
- Document the "always execute from project root" principle
- Note that all commands use root-relative paths (e.g., `uv run pytest app/tests/`)
- Document that `cd` commands should never be used in test commands
- Extract the pattern from `pyproject.toml` where `testpaths` and `pythonpath` enable this
- Note the Claude Code enforcement setting `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR: 1`
- Document how test files reference assets using root-relative paths (e.g., `"app/tests/assets/sample.dxf"`)

### Step 3: Document Test Configuration Patterns
- Extract pytest configuration from `pyproject.toml`:
  - `testpaths = ["app/tests"]` - Test discovery path
  - `pythonpath = ["app"]` - Module resolution path
- Document coverage configuration settings
- Note tool configurations (mypy, ruff) that support test code quality

### Step 4: Analyse Test File Patterns
- Document module docstring conventions describing test scope
- Extract class-based test organisation pattern (`class TestExtractor:`, `class TestBoundingBox:`)
- Document method naming: `test_<functionality>_<scenario>()`
- Note type hints on test methods (`def test_example(self) -> None:`)

### Step 4: Document Fixture Patterns
- Extract pytest fixture patterns:
  - `@pytest.fixture` decorator usage
  - `temp_dir` fixture yielding `tempfile.TemporaryDirectory`
  - Sample data fixtures returning typed dictionaries
- Document fixture generator scripts in `app/tests/assets/`
- Note static fixture files (`.dxf` files) and their creation scripts

### Step 5: Analyse Assertion Patterns
- Document assertion styles: `assert`, `pytest.raises`, `pytest.approx`
- Extract parametrized test patterns (`@pytest.mark.parametrize`)
- Note skip markers (`@pytest.mark.skip(reason="...")`)
- Document boundary/edge case testing patterns

### Step 6: Document Test Data Management
- Extract test asset organisation under `app/tests/assets/`
- Document fixture creation scripts pattern (Python scripts that generate test files)
- Note descriptive comments in fixture scripts explaining test scenarios
- Document the pattern of running scripts with `uv run <script>` to regenerate fixtures

### Step 7: Analyse Integration Test Patterns
- Document integration test approach (using real module interfaces)
- Note file I/O patterns with temp directories
- Extract cleanup patterns (finally blocks, context managers)
- Document mock usage patterns (`unittest.mock.patch`)

### Step 8: Create the Template Document
Create `ai_docs/010-testing-structure-template.md` with:
- Overview section explaining the testing philosophy
- Directory structure template (with variants for `tests/` at root vs `app/tests/` nested)
- Working directory convention section:
  - Always execute commands from project root - never use `cd` commands
  - Use `uv run <command>` with root-relative paths
  - All paths include appropriate prefix for consistency (e.g., `app/` or `tests/`)
  - File operations use root-relative paths
  - Scripts follow convention by executing from root without changing directories
  - Note: Enforced by Claude Code setting `CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR: 1`
- Configuration templates for `pyproject.toml` showing `testpaths` and `pythonpath` alignment
- Test file template with docstrings and class structure
- Fixture patterns with examples
- Assertion patterns and edge case testing
- Test asset management guidelines with root-relative paths
- Commands for running tests, coverage, and type checking (using root-relative paths)

### Step 9: Validate the Template
- Ensure the template is self-contained and can be applied to new projects
- Verify all examples are syntactically correct
- Check that the template aligns with the documented patterns in this codebase

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests to confirm nothing was broken during analysis
- `uv run mypy app/` - Run type checking to ensure test code passes type checks
- `test -f ai_docs/010-testing-structure-template.md && echo "Template created"` - Verify template file was created

## Notes
- The template should be generic enough to apply to any Python project while reflecting the best practices observed in this codebase
- The template should include rationale for each pattern to help developers understand why each practice is recommended
- Consider including common anti-patterns to avoid
- The template should reference pytest documentation where appropriate for further reading
- This codebase uses strict type checking with mypy; the template should reflect this in test method signatures
