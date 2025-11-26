# Bug: True Color (24-bit RGB) entities not extracted

## Bug Description
AutoCAD has two color systems: ACI (AutoCAD Color Index - 256 indexed colors) and True Color (24-bit RGB with 16.7 million colors). The current `_resolve_entity_color_to_rgb()` function in `app/core/extractor.py:82-154` only handles ACI colors. True Colors (like RGB 124,82,165 or 0,165,165) stored via DXF group code 420 or the `true_color` property are not being captured.

**Symptoms:**
- Entities with True Colors (24-bit RGB) are not included in color analysis output
- Only ACI colors (Index Colors from the 256-color palette) are extracted
- Missing color data for entities using the "True Color" tab in AutoCAD's color picker

**Expected behavior:** All entity colors should be extracted, whether they use ACI or True Color systems.

**Actual behavior:** Only entities with ACI colors or direct `entity.rgb` property are extracted. True Colors stored as packed 24-bit integers (group code 420) or via `entity.dxf.true_color` are ignored.

## Problem Statement
The `_resolve_entity_color_to_rgb()` function needs to handle True Color values stored in DXF files. True Colors are stored as:
1. Group code 420: A packed 24-bit integer where RGB = (value >> 16 & 0xFF, value >> 8 & 0xFF, value & 0xFF)
2. The `entity.dxf.true_color` attribute (available via ezdxf)

The current code only checks `entity.rgb` (line 116-120) which may not be populated for all True Color storage methods.

## Solution Statement
Extend `_resolve_entity_color_to_rgb()` to check for True Colors after the direct RGB check but before the ACI color handling. Use ezdxf's `entity.dxf.true_color` property to detect True Colors, which provides the packed 24-bit integer that can be unpacked to RGB values.

## Steps to Reproduce
1. Create a DXF file with entities using True Colors (via AutoCAD's "True Color" tab)
2. Run extraction on the file
3. Observe that True Color entities are missing from color analysis output

## Root Cause Analysis
The `_resolve_entity_color_to_rgb()` function at `app/core/extractor.py:82-154` has this logic:

1. **Line 116-120:** Checks `entity.rgb` for direct RGB - this works for some True Color cases but not all
2. **Line 122-148:** Falls through to ACI color handling (ByLayer, ByBlock, or color index)

The problem is that True Colors stored via group code 420 are accessible through `entity.dxf.true_color` as a packed integer, but this path is never checked. The `entity.rgb` property in ezdxf may return `None` even when a True Color is set via `true_color`.

When ezdxf encounters a True Color, it stores it in `entity.dxf.true_color` as an integer. The code needs to:
1. Check if `entity.dxf.true_color` exists and has a value
2. Unpack the 24-bit integer to RGB: `(value >> 16 & 0xFF, value >> 8 & 0xFF, value & 0xFF)`

## Relevant Files
Use these files to fix the bug:

- `app/core/extractor.py` - Contains `_resolve_entity_color_to_rgb()` function (lines 82-154) that needs modification to handle True Colors
- `app/tests/core/test_extractor.py` - Contains tests for color resolution that need True Color test cases added
- `app/tests/assets/` - Location for test fixture files

### New Files
- `app/tests/assets/true_color_test.dxf` - Test fixture with True Color entities
- `app/tests/assets/create_true_color_test.py` - Script to generate the True Color test fixture

## Step by Step Tasks

### Step 1: Create True Color test fixture generator
- Create `app/tests/assets/create_true_color_test.py` script that generates a DXF file with:
  - LINE entities with True Colors (using `entity.rgb = (R, G, B)` which internally sets true_color)
  - TEXT entities with True Colors
  - MTEXT entities with True Colors
  - Mix of True Colors and ACI colors on same layer
  - Use specific RGB values like (124, 82, 165) and (0, 165, 165) from the bug report
- Run the script to generate `app/tests/assets/true_color_test.dxf`

### Step 2: Modify _resolve_entity_color_to_rgb() to handle True Colors
- In `app/core/extractor.py`, modify the `_resolve_entity_color_to_rgb()` function
- After the existing `entity.rgb` check (lines 116-120), add a new check for `entity.dxf.true_color`:
  ```python
  # Check for True Color (group code 420 - packed 24-bit RGB)
  try:
      true_color = entity.dxf.get("true_color", None)
      if true_color is not None:
          # Unpack 24-bit integer to RGB
          r = (true_color >> 16) & 0xFF
          g = (true_color >> 8) & 0xFF
          b = true_color & 0xFF
          return (r, g, b)
  except (AttributeError, TypeError):
      pass
  ```
- Place this after the `entity.rgb` check but before the ACI color handling

### Step 3: Add unit tests for True Color extraction
- In `app/tests/core/test_extractor.py`, add tests:
  - `test_resolve_entity_color_to_rgb_true_color()` - Test True Color extraction from entities
  - `test_true_color_in_annotation_data()` - Verify True Colors appear in annotation_data
  - `test_true_color_in_color_analysis()` - Verify True Colors appear in color_analysis_data
  - `test_true_color_mixed_with_aci()` - Verify both True Color and ACI entities are extracted correctly

### Step 4: Run validation commands
- Run all tests to ensure the fix works and no regressions occur
- Run type checking and linting

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `uv run python app/tests/assets/create_true_color_test.py` - Generate the True Color test fixture
- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests including new True Color tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify no regressions
- `uv run mypy app/` - Type check the codebase
- `uv run ruff check app/` - Lint the codebase

## Notes
- The ezdxf library stores True Colors as 24-bit packed integers in `entity.dxf.true_color`
- Use `entity.dxf.get("true_color", None)` for safe access since not all entities have this attribute
- The `entity.rgb` property may already work for some True Color cases where ezdxf exposes it, but `true_color` is more reliable
- ACI color 256 (ByLayer) and 0 (ByBlock) are special cases already handled in the existing code
- No new dependencies are needed - ezdxf already supports True Color access
