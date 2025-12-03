# Chore: Refactor test_excel_formatting.py Into Subdirectory Modules

## Chore Description
The file `app/tests/core/test_excel_formatting.py` (1657 lines) exceeds the 1000-line threshold and needs to be split into smaller, focused test modules. This chore creates a new `app/tests/core/excel_formatting/` subdirectory and splits the 7 test classes into 4 separate modules organized by feature. The shared `temp_dir` fixture is extracted to conftest.py. The refactoring follows pytest conventions and maintains 100% test coverage and backward compatibility.

## Relevant Files
Use these files to resolve the chore:

- `app/tests/core/test_excel_formatting.py` - Source file to split (1657 lines). Contains 7 test classes with `temp_dir` fixture that needs extraction to conftest.py.
- `ai_docs/001-naming-convention-guide.md` - Project naming conventions to follow during refactoring.

### New Files

**Subdirectory: `app/tests/core/excel_formatting/`**
- `__init__.py` - Empty init file for Python package
- `conftest.py` - Shared fixtures:
  - `temp_dir` - Creates temporary directory (used by 5 test classes)
- `test_formatting_header.py` - TestFormatHeader class (~57 lines, lines 35-91 from original)
- `test_formatting_sheets.py` - TestBlockAnalysisFormatting + TestLayerAnalysisFormatting + TestEntitySummaryFormatting + TestBlockGeometryAnalysisFormatting (~838 lines, lines 92-929)
- `test_formatting_scale.py` - TestNegativeScaleHighlighting class (~423 lines, lines 930-1352)
- `test_formatting_annotations.py` - TestAnnotationsAnalysisFormatting class (~305 lines, lines 1353-1657)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create excel_formatting test subdirectory structure
- Create directory `app/tests/core/excel_formatting/`
- Create empty `app/tests/core/excel_formatting/__init__.py`

### Step 2: Create conftest.py with shared fixture
- Create `app/tests/core/excel_formatting/conftest.py`
- Add the following content:
  ```python
  """Shared fixtures for excel_formatting tests."""

  import tempfile
  from typing import Iterator

  import pytest


  @pytest.fixture
  def temp_dir() -> Iterator[str]:
      """Create a temporary directory for test outputs."""
      with tempfile.TemporaryDirectory() as tmpdir:
          yield tmpdir
  ```

### Step 3: Create test_formatting_header.py
- Create `app/tests/core/excel_formatting/test_formatting_header.py`
- Copy the docstring and imports from original file (lines 1-33):
  ```python
  """
  Unit tests for the excel_formatting module - header formatting.
  """

  from core.excel_formatting import format_header
  ```
- Copy the entire `TestFormatHeader` class (lines 35-91)
- This class has no fixtures and is self-contained

### Step 4: Create test_formatting_sheets.py
- Create `app/tests/core/excel_formatting/test_formatting_sheets.py`
- Copy imports from original file (lines 1-33)
- Copy these four sheet-formatting test classes:
  - `TestBlockAnalysisFormatting` class (lines 92-164, ~73 lines)
  - `TestLayerAnalysisFormatting` class (lines 165-248, ~84 lines)
  - `TestEntitySummaryFormatting` class (lines 249-304, ~56 lines)
  - `TestBlockGeometryAnalysisFormatting` class (lines 305-929, ~625 lines)
- Remove duplicate `temp_dir` fixture definitions from each class (now in conftest.py)
- These classes test the sheet-specific formatting functions and belong together logically

### Step 5: Create test_formatting_scale.py
- Create `app/tests/core/excel_formatting/test_formatting_scale.py`
- Copy imports from original file
- Copy `TestNegativeScaleHighlighting` class (lines 930-1352, ~423 lines)
- Remove `temp_dir` fixture definition (now in conftest.py)
- This class tests negative scale highlighting functionality

### Step 6: Create test_formatting_annotations.py
- Create `app/tests/core/excel_formatting/test_formatting_annotations.py`
- Copy imports from original file
- Copy `TestAnnotationsAnalysisFormatting` class (lines 1353-1657, ~305 lines)
- This class has no fixtures and is self-contained (uses Workbook directly, not temp_dir)
- This class tests the annotations analysis sheet formatting

### Step 7: Verify new tests pass
- Run `uv run pytest app/tests/core/excel_formatting/ -v` to verify all new excel_formatting tests pass
- Count tests to ensure none were lost

### Step 8: Delete original file
- Delete `app/tests/core/test_excel_formatting.py`

### Step 9: Run validation commands
- Execute all validation commands listed below

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_formatting/ -v` - Run new excel_formatting tests to verify split was successful
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run pytest --cov=app/core app/tests/` - Verify test coverage remains unchanged
- `wc -l app/tests/core/excel_formatting/*.py` - Verify no new file exceeds 1000 lines
- `uv run mypy app/` - Verify type checking passes

## Notes

- The `temp_dir` fixture is duplicated in 5 test classes - extracting to conftest.py removes this duplication.
- `TestFormatHeader` and `TestAnnotationsAnalysisFormatting` don't use `temp_dir` - they create Workbooks directly in memory.
- Fixtures in conftest.py are automatically discovered by pytest - no explicit imports needed in test modules.
- All imports should use `from core.excel_formatting import ...` format (not relative imports) for consistency with existing patterns.
- Line numbers are approximate - verify by searching for class definitions like `class TestFormatHeader:`.
- The sheet formatting classes (TestBlockAnalysisFormatting, TestLayerAnalysisFormatting, TestEntitySummaryFormatting, TestBlockGeometryAnalysisFormatting) are grouped together because they all test sheet-specific formatting functions.
- `TestBlockGeometryAnalysisFormatting` is the largest class (~625 lines) but still under 1000 lines when isolated.
