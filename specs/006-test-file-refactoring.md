# Chore: Split Large Test Files Under 1000 Lines

## Chore Description
Three test files exceed the 1000-line threshold: `test_extractor.py` (2460 lines), `test_excel_writer.py` (2435 lines), and `test_excel_formatting.py` (1657 lines). This chore refactors each file by splitting test classes into separate modules within feature-specific subdirectories. The refactoring follows pytest conventions and existing naming patterns while maintaining 100% test coverage and backward compatibility.

## Relevant Files
Use these files to resolve the chore:

- `app/tests/core/test_extractor.py` - 2460 lines with 7 test classes (TestExtractor, TestColorAnalysis, TestMtextFormatting, TestTrueColorExtraction, TestHatchExtraction, TestAciExtraction, TestDynamicBlockExtraction). Will be split into 5 modules.
- `app/tests/core/test_excel_writer.py` - 2435 lines with 8 test classes (TestExcelWriter, TestNegativeScaleDetection, TestNegativeScaleTextGeneration, TestNegativeScaleIntegration, TestAnnotationsAnalysisSheet, TestAciDisplayNameMapping, TestColorAnalysisExcelOutput, TestExtractionIssuesSheet). Will be split into 5 modules.
- `app/tests/core/test_excel_formatting.py` - 1657 lines with 7 test classes (TestFormatHeader, TestBlockAnalysisFormatting, TestLayerAnalysisFormatting, TestEntitySummaryFormatting, TestBlockGeometryAnalysisFormatting, TestNegativeScaleHighlighting, TestAnnotationsAnalysisFormatting). Will be split into 4 modules.
- `ai_docs/001-naming-convention-guide.md` - Project naming conventions to follow during refactoring.
- `ai_output/001-test-file-refactoring-analysis.md` - Detailed analysis with class line numbers and recommended module splits.

### New Files

**Subdirectory: `app/tests/core/extractor/`**
- `__init__.py` - Empty init file
- `conftest.py` - Shared fixtures for extractor tests
- `test_extractor_core.py` - TestExtractor class (lines 33-1182)
- `test_extractor_color.py` - TestColorAnalysis + TestTrueColorExtraction + TestAciExtraction (lines 1183-1437, 1728-1953, 2113-2272)
- `test_extractor_mtext.py` - TestMtextFormatting class (lines 1438-1727)
- `test_extractor_hatch.py` - TestHatchExtraction class (lines 1954-2112)
- `test_extractor_dynamic.py` - TestDynamicBlockExtraction class (lines 2273-2460)

**Subdirectory: `app/tests/core/excel_writer/`**
- `__init__.py` - Empty init file
- `conftest.py` - Shared fixtures (temp_dir, sample_extraction_data, annotation_extraction_data, color_analysis_data, extraction_issues_data, no_issues_data)
- `test_excel_writer_core.py` - TestExcelWriter class (lines 62-1331)
- `test_excel_writer_scale.py` - TestNegativeScaleDetection + TestNegativeScaleTextGeneration + TestNegativeScaleIntegration (lines 1332-1733)
- `test_excel_writer_annotations.py` - TestAnnotationsAnalysisSheet class (lines 1734-1992)
- `test_excel_writer_color.py` - TestAciDisplayNameMapping + TestColorAnalysisExcelOutput (lines 1993-2194)
- `test_excel_writer_issues.py` - TestExtractionIssuesSheet class (lines 2195-2435)

**Subdirectory: `app/tests/core/excel_formatting/`**
- `__init__.py` - Empty init file
- `conftest.py` - Shared fixtures (temp_dir)
- `test_formatting_header.py` - TestFormatHeader class (lines 35-91)
- `test_formatting_sheets.py` - TestBlockAnalysisFormatting + TestLayerAnalysisFormatting + TestEntitySummaryFormatting + TestBlockGeometryAnalysisFormatting (lines 92-929)
- `test_formatting_scale.py` - TestNegativeScaleHighlighting class (lines 930-1352)
- `test_formatting_annotations.py` - TestAnnotationsAnalysisFormatting class (lines 1353-1657)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create extractor test subdirectory structure
- Create directory `app/tests/core/extractor/`
- Create empty `app/tests/core/extractor/__init__.py`
- Create `app/tests/core/extractor/conftest.py` with any shared fixtures from test_extractor.py (none currently - just empty conftest)

### Step 2: Split test_extractor.py into 5 modules
- Create `app/tests/core/extractor/test_extractor_core.py`:
  - Copy imports from original file
  - Copy TestExtractor class (lines 33-1182)
  - Ensure all imports used by this class are included
- Create `app/tests/core/extractor/test_extractor_color.py`:
  - Copy imports from original file
  - Copy TestColorAnalysis class (lines 1183-1437)
  - Copy TestTrueColorExtraction class (lines 1728-1953)
  - Copy TestAciExtraction class (lines 2113-2272)
- Create `app/tests/core/extractor/test_extractor_mtext.py`:
  - Copy imports from original file
  - Copy TestMtextFormatting class (lines 1438-1727)
- Create `app/tests/core/extractor/test_extractor_hatch.py`:
  - Copy imports from original file
  - Copy TestHatchExtraction class (lines 1954-2112)
- Create `app/tests/core/extractor/test_extractor_dynamic.py`:
  - Copy imports from original file
  - Copy TestDynamicBlockExtraction class (lines 2273-2460)

### Step 3: Create excel_writer test subdirectory structure
- Create directory `app/tests/core/excel_writer/`
- Create empty `app/tests/core/excel_writer/__init__.py`
- Create `app/tests/core/excel_writer/conftest.py` with shared fixtures:
  - `temp_dir` fixture (used by multiple classes)
  - `sample_extraction_data` fixture (from TestExcelWriter)
  - `annotation_extraction_data` fixture (from TestAnnotationsAnalysisSheet)
  - `color_analysis_data` fixture (from TestColorAnalysisExcelOutput)
  - `extraction_issues_data` fixture (from TestExtractionIssuesSheet)
  - `no_issues_data` fixture (from TestExtractionIssuesSheet)

### Step 4: Split test_excel_writer.py into 5 modules
- Create `app/tests/core/excel_writer/test_excel_writer_core.py`:
  - Copy imports from original file
  - Copy TestExcelWriter class (lines 62-1331)
  - Remove class-level fixtures now in conftest.py
- Create `app/tests/core/excel_writer/test_excel_writer_scale.py`:
  - Copy imports from original file
  - Copy TestNegativeScaleDetection class (lines 1332-1386)
  - Copy TestNegativeScaleTextGeneration class (lines 1387-1616)
  - Copy TestNegativeScaleIntegration class (lines 1617-1733)
- Create `app/tests/core/excel_writer/test_excel_writer_annotations.py`:
  - Copy imports from original file
  - Copy TestAnnotationsAnalysisSheet class (lines 1734-1992)
- Create `app/tests/core/excel_writer/test_excel_writer_color.py`:
  - Copy imports from original file
  - Copy TestAciDisplayNameMapping class (lines 1993-2045)
  - Copy TestColorAnalysisExcelOutput class (lines 2046-2194)
- Create `app/tests/core/excel_writer/test_excel_writer_issues.py`:
  - Copy imports from original file
  - Copy TestExtractionIssuesSheet class (lines 2195-2435)

### Step 5: Create excel_formatting test subdirectory structure
- Create directory `app/tests/core/excel_formatting/`
- Create empty `app/tests/core/excel_formatting/__init__.py`
- Create `app/tests/core/excel_formatting/conftest.py` with shared fixtures:
  - `temp_dir` fixture (used by multiple classes)

### Step 6: Split test_excel_formatting.py into 4 modules
- Create `app/tests/core/excel_formatting/test_formatting_header.py`:
  - Copy imports from original file
  - Copy TestFormatHeader class (lines 35-91)
- Create `app/tests/core/excel_formatting/test_formatting_sheets.py`:
  - Copy imports from original file
  - Copy TestBlockAnalysisFormatting class (lines 92-164)
  - Copy TestLayerAnalysisFormatting class (lines 165-248)
  - Copy TestEntitySummaryFormatting class (lines 249-304)
  - Copy TestBlockGeometryAnalysisFormatting class (lines 305-929)
- Create `app/tests/core/excel_formatting/test_formatting_scale.py`:
  - Copy imports from original file
  - Copy TestNegativeScaleHighlighting class (lines 930-1352)
- Create `app/tests/core/excel_formatting/test_formatting_annotations.py`:
  - Copy imports from original file
  - Copy TestAnnotationsAnalysisFormatting class (lines 1353-1657)

### Step 7: Run tests to verify all modules work
- Run `uv run pytest app/tests/core/extractor/ -v` to verify extractor tests
- Run `uv run pytest app/tests/core/excel_writer/ -v` to verify excel_writer tests
- Run `uv run pytest app/tests/core/excel_formatting/ -v` to verify excel_formatting tests

### Step 8: Remove original large test files
- Delete `app/tests/core/test_extractor.py`
- Delete `app/tests/core/test_excel_writer.py`
- Delete `app/tests/core/test_excel_formatting.py`

### Step 9: Final validation
- Run full test suite: `uv run pytest app/tests/ -v`
- Run coverage check: `uv run pytest --cov=app/core app/tests/`
- Verify no file exceeds 1000 lines: `find app/tests -name "*.py" -exec wc -l {} \; | sort -n | tail -10`

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/ -v` - Run all tests to verify no regressions after refactoring
- `uv run pytest --cov=app/core app/tests/` - Verify test coverage remains unchanged
- `find app/tests -name "*.py" -exec wc -l {} \; | sort -n | tail -10` - Verify no test file exceeds 1000 lines
- `uv run mypy app/` - Verify type checking passes

## Notes

- The `temp_dir` fixture is duplicated across multiple test classes. Moving it to conftest.py will reduce duplication and ensure consistency.
- Fixtures in conftest.py are automatically discovered by pytest - no explicit imports needed in test modules.
- Test file assets remain in `app/tests/assets/` and don't need to be moved.
- The existing `app/tests/core/test_geometry.py` (447 lines) and `app/tests/core/test_logger.py` (328 lines) are under 1000 lines and don't need refactoring.
- All imports should use `from core.extractor import ...` format (not relative imports) for consistency with existing patterns.
- When creating conftest.py files, include the necessary imports for the fixture types (e.g., `Iterator`, `tempfile`, `ExtractionResult`).
