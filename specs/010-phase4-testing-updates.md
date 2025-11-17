# Chore: Update Tests to Use Proper Working Directory Convention

## Chore Description
Phase 4 testing is already at 91% coverage and comprehensive, but the existing tests violate the project's working directory convention. The tests currently rely on `conftest.py` to change directories to `app/`, but the project standard requires all commands to run from the project root with root-relative paths (using `app/` prefix).

This chore updates the test suite to:
1. Remove the directory-changing conftest.py
2. Update all test file paths to use root-relative paths with `app/` prefix
3. Validate tests still pass with >80% coverage (currently at 91%)
4. Ensure tests follow the same convention as all other project commands

## Relevant Files
Use these files to resolve the chore:

- **conftest.py** - Currently changes working directory to `app/`, needs to be removed or updated to not change directories
- **app/tests/core/test_extractor.py** - Uses relative paths like `tests/assets/sample_drawing.dxf`, needs to be updated to `app/tests/assets/sample_drawing.dxf`
- **app/tests/core/test_excel_writer.py** - Already uses temp directories, should not need path changes but needs validation
- **README.md** - Documents the working directory convention that tests must follow

### Analysis
Current test paths that need updating in `test_extractor.py`:
- Line 24: `'tests/assets/sample_drawing.dxf'` → `'app/tests/assets/sample_drawing.dxf'`
- Line 39: `'tests/assets/empty_drawing.dxf'` → `'app/tests/assets/empty_drawing.dxf'`
- Line 49: `'tests/assets/invalid.dxf'` → `'app/tests/assets/invalid.dxf'`
- Line 54: `'tests/assets/nonexistent.dxf'` → `'app/tests/assets/nonexistent.dxf'`
- Line 58: `'tests/assets/sample_drawing.dxf'` → `'app/tests/assets/sample_drawing.dxf'`
- Line 71: `'tests/assets/sample_drawing.dxf'` → `'app/tests/assets/sample_drawing.dxf'`
- Line 87: `Path('tests/assets/test.txt')` → `Path('app/tests/assets/test.txt')`
- Line 104: `'tests/assets/Supermarket-2020.dwg'` → `'app/tests/assets/Supermarket-2020.dwg'`

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Delete conftest.py
- Delete the `conftest.py` file from the project root
- The file only contains directory-changing logic that violates project convention
- pytest will run tests from project root without requiring this configuration file

### Step 2: Update test_extractor.py File Paths
- Replace all occurrences of `'tests/assets/` with `'app/tests/assets/` in test_extractor.py
- Update the `Path('tests/assets/test.txt')` temporary file path to use root-relative path
- Ensure all 8 path references are updated

### Step 3: Verify test_excel_writer.py Paths
- Review test_excel_writer.py to confirm it uses temp directories (no relative path changes needed)
- Verify no hardcoded relative paths that would break with the conftest.py change

### Step 4: Run Validation Commands
- Execute all validation commands to ensure tests pass with >80% coverage
- Verify zero regressions from the path updates

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/` - Run all tests from project root to validate they pass with new paths
- `uv run pytest --cov=app/core app/tests/ --cov-report=term-missing` - Verify coverage remains >80% (target: 91% maintained)
- `uv run pytest app/tests/core/test_extractor.py -v` - Validate extractor tests pass with updated paths
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Validate excel writer tests remain unaffected

## Notes
- Current coverage is 91% (95 statements, 9 uncovered)
  - app/core/excel_writer.py: 85% coverage (lines 102-107 uncovered - exception handling)
  - app/core/extractor.py: 91% coverage (lines 86-88 uncovered - exception handling)
  - All other modules: 100% coverage
- The uncovered lines are generic exception handlers which are acceptable to leave uncovered
- After this chore, tests will align with the project convention documented in README.md lines 51-60
- This ensures consistency: all commands (pytest, python, scripts) run from project root with `app/` prefix
