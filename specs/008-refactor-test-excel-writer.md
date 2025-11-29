# Chore: Refactor test_excel_writer.py Into Subdirectory Modules

## Chore Description
The file `app/tests/core/test_excel_writer.py` (2435 lines) exceeds the 1000-line threshold and needs to be split into smaller, focused test modules. This chore creates a new `app/tests/core/excel_writer/` subdirectory and splits the 8 test classes into 5 separate modules organized by feature. Shared fixtures (temp_dir, sample_extraction_data, etc.) are extracted to conftest.py. The refactoring follows pytest conventions and maintains 100% test coverage and backward compatibility.

## Relevant Files
Use these files to resolve the chore:

- `app/tests/core/test_excel_writer.py` - Source file to split (2435 lines). Contains 8 test classes with fixtures that need extraction to conftest.py.
- `ai_docs/001-naming-convention-guide.md` - Project naming conventions to follow during refactoring.
- `app/tests/assets/` - Test DXF fixture files used by tests (remain unchanged).

### New Files

**Subdirectory: `app/tests/core/excel_writer/`**
- `__init__.py` - Empty init file for Python package
- `conftest.py` - Shared fixtures extracted from test classes:
  - `temp_dir` - Creates temporary directory (used by all classes)
  - `sample_extraction_data` - Basic extraction data (from TestExcelWriter, line 72)
  - `annotation_extraction_data` - Extraction data with annotations (from TestAnnotationsAnalysisSheet, line 1744)
  - `color_analysis_data` - Extraction data with color records (from TestColorAnalysisExcelOutput, line 2056)
  - `extraction_issues_data` - Extraction data with issues (from TestExtractionIssuesSheet, line 2205)
  - `no_issues_data` - Extraction data without issues (from TestExtractionIssuesSheet, line 2254)
- `test_excel_writer_core.py` - TestExcelWriter class (~1270 lines, lines 62-1331 from original)
- `test_excel_writer_scale.py` - TestNegativeScaleDetection + TestNegativeScaleTextGeneration + TestNegativeScaleIntegration (~400 lines, lines 1332-1733)
- `test_excel_writer_annotations.py` - TestAnnotationsAnalysisSheet class (~260 lines, lines 1734-1992)
- `test_excel_writer_color.py` - TestAciDisplayNameMapping + TestColorAnalysisExcelOutput (~200 lines, lines 1993-2194)
- `test_excel_writer_issues.py` - TestExtractionIssuesSheet class (~240 lines, lines 2195-2435)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create excel_writer test subdirectory structure
- Create directory `app/tests/core/excel_writer/`
- Create empty `app/tests/core/excel_writer/__init__.py`

### Step 2: Create conftest.py with shared fixtures
- Create `app/tests/core/excel_writer/conftest.py`
- Add the following imports:
  ```python
  """Shared fixtures for excel_writer tests."""

  import tempfile
  from typing import Iterator

  import pytest

  from core.extractor import ExtractionResult
  from core.types import AnnotationKey, BlockLayerKey, BlockRotationKey
  ```
- Extract and add `temp_dir` fixture (lines 66-69):
  ```python
  @pytest.fixture
  def temp_dir() -> Iterator[str]:
      """Create a temporary directory for test outputs."""
      with tempfile.TemporaryDirectory() as tmpdir:
          yield tmpdir
  ```
- Extract and add `sample_extraction_data` fixture (lines 72-137 from TestExcelWriter)
- Extract and add `annotation_extraction_data` fixture (lines 1744-1802 from TestAnnotationsAnalysisSheet)
- Extract and add `color_analysis_data` fixture (lines 2056-2115 from TestColorAnalysisExcelOutput)
- Extract and add `extraction_issues_data` fixture (lines 2205-2251 from TestExtractionIssuesSheet)
- Extract and add `no_issues_data` fixture (lines 2254-2285 from TestExtractionIssuesSheet)

### Step 3: Create test_excel_writer_core.py
- Create `app/tests/core/excel_writer/test_excel_writer_core.py`
- Copy the docstring and all imports from original file (lines 1-59)
- Copy the entire `TestExcelWriter` class (lines 62-1331)
- Remove the `temp_dir` and `sample_extraction_data` fixture definitions (now in conftest.py)
- The fixtures will be auto-discovered by pytest from conftest.py

### Step 4: Create test_excel_writer_scale.py
- Create `app/tests/core/excel_writer/test_excel_writer_scale.py`
- Copy imports from original file
- Copy these three scale-related test classes:
  - `TestNegativeScaleDetection` class (lines 1332-1386, ~55 lines)
  - `TestNegativeScaleTextGeneration` class (lines 1387-1616, ~230 lines)
  - `TestNegativeScaleIntegration` class (lines 1617-1733, ~117 lines)
- Remove duplicate `temp_dir` fixture definitions from each class (now in conftest.py)

### Step 5: Create test_excel_writer_annotations.py
- Create `app/tests/core/excel_writer/test_excel_writer_annotations.py`
- Copy imports from original file
- Copy `TestAnnotationsAnalysisSheet` class (lines 1734-1992, ~259 lines)
- Remove `temp_dir` and `annotation_extraction_data` fixtures (now in conftest.py)

### Step 6: Create test_excel_writer_color.py
- Create `app/tests/core/excel_writer/test_excel_writer_color.py`
- Copy imports from original file
- Copy these two color-related test classes:
  - `TestAciDisplayNameMapping` class (lines 1993-2045, ~53 lines)
  - `TestColorAnalysisExcelOutput` class (lines 2046-2194, ~149 lines)
- Remove `temp_dir` and `color_analysis_data` fixtures (now in conftest.py)

### Step 7: Create test_excel_writer_issues.py
- Create `app/tests/core/excel_writer/test_excel_writer_issues.py`
- Copy imports from original file
- Copy `TestExtractionIssuesSheet` class (lines 2195-2435, ~241 lines)
- Remove `temp_dir`, `extraction_issues_data`, and `no_issues_data` fixtures (now in conftest.py)

### Step 8: Verify new tests pass
- Run `uv run pytest app/tests/core/excel_writer/ -v` to verify all new excel_writer tests pass
- Count tests to ensure none were lost

### Step 9: Delete original file
- Delete `app/tests/core/test_excel_writer.py`

### Step 10: Run validation commands
- Execute all validation commands listed below

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/excel_writer/ -v` - Run new excel_writer tests to verify split was successful
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run pytest --cov=app/core app/tests/` - Verify test coverage remains unchanged
- `wc -l app/tests/core/excel_writer/*.py` - Verify no new file exceeds 1000 lines
- `uv run mypy app/` - Verify type checking passes

## Notes

- The `temp_dir` fixture is duplicated in 6 test classes - extracting to conftest.py removes this duplication.
- Fixtures in conftest.py are automatically discovered by pytest - no explicit imports needed in test modules.
- When a test class method has a `temp_dir` parameter, pytest will inject the fixture from conftest.py.
- Test file assets in `app/tests/assets/` are referenced with paths like `"app/tests/assets/sample_drawing.dxf"` and don't need modification.
- All imports should use `from core.excel_writer import ...` format (not relative imports) for consistency with existing patterns.
- Some fixtures have internal imports (e.g., `from core.types import AnnotationKey`) that need to be moved to the top of conftest.py.
- Line numbers are approximate - verify by searching for class definitions like `class TestExcelWriter:`.
- The scale-related classes (TestNegativeScaleDetection, TestNegativeScaleTextGeneration, TestNegativeScaleIntegration) are grouped together because they all test negative scale handling.
