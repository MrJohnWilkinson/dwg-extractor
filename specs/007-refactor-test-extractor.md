# Chore: Refactor test_extractor.py Into Subdirectory Modules

## Chore Description
The file `app/tests/core/test_extractor.py` (2460 lines) exceeds the 1000-line threshold and needs to be split into smaller, focused test modules. This chore creates a new `app/tests/core/extractor/` subdirectory and splits the 7 test classes into 5 separate modules organized by feature. The refactoring follows pytest conventions and maintains 100% test coverage and backward compatibility.

## Relevant Files
Use these files to resolve the chore:

- `app/tests/core/test_extractor.py` - Source file to split (2460 lines). Contains 7 test classes that will be distributed across 5 new modules.
- `ai_docs/001-naming-convention-guide.md` - Project naming conventions to follow during refactoring.
- `app/tests/assets/` - Test DXF fixture files used by tests (remain unchanged).

### New Files

**Subdirectory: `app/tests/core/extractor/`**
- `__init__.py` - Empty init file for Python package
- `conftest.py` - Shared fixtures for extractor tests (currently none needed - create empty)
- `test_extractor_core.py` - TestExtractor class (~1150 lines, lines 33-1182 from original)
- `test_extractor_color.py` - TestColorAnalysis + TestTrueColorExtraction + TestAciExtraction (~700 lines combined)
- `test_extractor_mtext.py` - TestMtextFormatting class (~290 lines, lines 1438-1727 from original)
- `test_extractor_hatch.py` - TestHatchExtraction class (~160 lines, lines 1954-2112 from original)
- `test_extractor_dynamic.py` - TestDynamicBlockExtraction class (~190 lines, lines 2273-2460 from original)

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create extractor test subdirectory structure
- Create directory `app/tests/core/extractor/`
- Create empty `app/tests/core/extractor/__init__.py`
- Create empty `app/tests/core/extractor/conftest.py` (no shared fixtures currently needed)

### Step 2: Create test_extractor_core.py
- Create `app/tests/core/extractor/test_extractor_core.py`
- Copy the docstring and imports from original file (lines 1-31):
  ```python
  """
  Unit tests for the extractor module - core functionality.
  """

  from pathlib import Path

  import ezdxf
  import pytest

  from core.extractor import (
      _clean_mtext_content,
      _resolve_entity_color_to_rgb,
      _resolve_entity_color_with_aci,
      extract_blocks,
  )
  from core.geometry import (
      _calculate_segments,
      _categorize_rotation,
      _get_block_bounding_box,
      _get_intersection_points,
  )
  from core.types import AnnotationKey, BlockLayerKey, BlockRotationKey
  ```
- Copy the entire `TestExtractor` class (lines 33-1182)
- Verify all imports used by this class are included

### Step 3: Create test_extractor_color.py
- Create `app/tests/core/extractor/test_extractor_color.py`
- Copy imports from original file
- Copy these three color-related test classes:
  - `TestColorAnalysis` class (lines 1183-1437, ~255 lines)
  - `TestTrueColorExtraction` class (lines 1728-1953, ~226 lines)
  - `TestAciExtraction` class (lines 2113-2272, ~160 lines)
- These classes test color extraction features and belong together logically

### Step 4: Create test_extractor_mtext.py
- Create `app/tests/core/extractor/test_extractor_mtext.py`
- Copy imports from original file
- Copy `TestMtextFormatting` class (lines 1438-1727, ~290 lines)
- This class tests MTEXT formatting and parsing

### Step 5: Create test_extractor_hatch.py
- Create `app/tests/core/extractor/test_extractor_hatch.py`
- Copy imports from original file
- Copy `TestHatchExtraction` class (lines 1954-2112, ~159 lines)
- This class tests hatch entity extraction

### Step 6: Create test_extractor_dynamic.py
- Create `app/tests/core/extractor/test_extractor_dynamic.py`
- Copy imports from original file
- Copy `TestDynamicBlockExtraction` class (lines 2273-2460, ~188 lines)
- This class tests dynamic block and XDATA extraction

### Step 7: Verify new tests pass
- Run `uv run pytest app/tests/core/extractor/ -v` to verify all new extractor tests pass
- Count tests to ensure none were lost

### Step 8: Delete original file
- Delete `app/tests/core/test_extractor.py`

### Step 9: Run validation commands
- Execute all validation commands listed below

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/extractor/ -v` - Run new extractor tests to verify split was successful
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run pytest --cov=app/core app/tests/` - Verify test coverage remains unchanged
- `wc -l app/tests/core/extractor/*.py` - Verify no new file exceeds 1000 lines
- `uv run mypy app/` - Verify type checking passes

## Notes

- The test_extractor.py file has no shared fixtures that need to be moved to conftest.py - each test class is self-contained.
- Test file assets in `app/tests/assets/` are referenced with paths like `"app/tests/assets/sample_drawing.dxf"` and don't need modification.
- All imports should use `from core.extractor import ...` format (not relative imports) for consistency with existing patterns.
- The color-related test classes (TestColorAnalysis, TestTrueColorExtraction, TestAciExtraction) are grouped together because they all test color extraction functionality.
- Line numbers are approximate - verify by searching for class definitions like `class TestExtractor:`.
