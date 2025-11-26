# Feature: AutoCAD Color Name Column

## Feature Description
Add a new "Color Autocad Name" column to the Color Analysis sheet that displays human-readable AutoCAD color names alongside RGB values. This allows users to easily match colors in the Excel export to their original AutoCAD drawing settings without manually looking up ACI (AutoCAD Color Index) values.

## User Story
As a user viewing the Color Analysis sheet,
I want to see the AutoCAD color name alongside RGB values,
So that I can easily match colors to my AutoCAD drawing settings.

## Problem Statement
Currently, the Color Analysis sheet displays RGB values (Red, Green, Blue) and a color sample, but users cannot easily determine which AutoCAD color was used. AutoCAD uses a standardized 256-color palette (ACI - AutoCAD Color Index) where colors 1-7 have named colors (Red, Yellow, Green, Cyan, Blue, Magenta, White) and higher indices are numbered. Without seeing the ACI name, users must manually cross-reference RGB values with AutoCAD's color palette to understand the original color specification.

## Solution Statement
Track the ACI (AutoCAD Color Index) value during color extraction in `extractor.py`, then map it to a human-readable name using a new utility function. The mapping follows AutoCAD's standard naming:
- ACI 0: "ByBlock"
- ACI 1-7: Named colors (Red, Yellow, Green, Cyan, Blue, Magenta, White)
- ACI 8-255: "Color N" format (e.g., "Color 30", "Color 220")
- ACI 256: "ByLayer"
- ACI None: "True Color" (for 24-bit RGB colors that bypass the ACI palette)

The new column will appear after "Color Sample" in the Color Analysis sheet.

## Relevant Files
Use these files to implement the feature:

- `app/core/types.py` - Add `color_aci` field to `ColorAnalysisRecord` TypedDict
- `app/core/extractor.py` - Modify `_resolve_entity_color_to_rgb()` to also return ACI value, update `extract_color_analysis()` to capture ACI
- `app/core/constants.py` - Add `EXCEL_COLUMN_COLOR_AUTOCAD_NAME` constant
- `app/core/excel_writer.py` - Add new column to `_create_color_analysis_sheet()` with ACI-to-name mapping
- `app/core/excel_formatting.py` - Update `_format_color_analysis_sheet()` to handle new column width and position
- `app/tests/core/test_extractor.py` - Add tests for ACI value extraction
- `app/tests/core/test_excel_writer.py` - Add tests for new column output
- `app/tests/core/test_excel_formatting.py` - Add tests for column formatting

### New Files
None required - all changes are modifications to existing files.

## Implementation Plan
### Phase 1: Foundation
1. Update `ColorAnalysisRecord` TypedDict to include `color_aci: int | None` field (None for True Color entities)
2. Refactor `_resolve_entity_color_to_rgb()` to return both RGB and ACI values
3. Add `EXCEL_COLUMN_COLOR_AUTOCAD_NAME` constant following naming conventions

### Phase 2: Core Implementation
1. Update `extract_color_analysis()` to capture and store ACI values in records
2. Create `_get_aci_display_name()` function to map ACI indices to display names
3. Update `_create_color_analysis_sheet()` to include the new column with mapped names

### Phase 3: Integration
1. Update `_format_color_analysis_sheet()` to set appropriate column width
2. Adjust column letter references in formatting (column positions shift)
3. Write comprehensive tests for all new functionality

## Step by Step Tasks

### Step 1: Update ColorAnalysisRecord TypedDict
- Add `color_aci: int | None` field to `ColorAnalysisRecord` in `app/core/types.py`
- None indicates True Color (24-bit RGB) which has no ACI index
- Update docstring to document the new field

### Step 2: Add Excel Column Constant
- Add `EXCEL_COLUMN_COLOR_AUTOCAD_NAME: str = "color_autocad_name"` to `app/core/constants.py`
- Place it after `EXCEL_COLUMN_COLOR_SAMPLE` to maintain logical grouping

### Step 3: Refactor _resolve_entity_color_to_rgb to Return ACI
- Create new function `_resolve_entity_color_with_aci()` that returns `tuple[tuple[int, int, int], int | None] | None`
- Return tuple of (rgb_tuple, aci_value) or None; aci_value is None for True Color entities
- Keep existing `_resolve_entity_color_to_rgb()` as a wrapper for backwards compatibility
- Handle special cases: ByBlock (0), ByLayer (256), direct ACI (1-255), and True Color (returns None for ACI)

### Step 4: Update extract_color_analysis() to Capture ACI
- Modify `extract_color_analysis()` to use `_resolve_entity_color_with_aci()`
- Include `color_aci` in all `ColorAnalysisRecord` entries
- Ensure geometric entities and text entities both capture ACI values

### Step 5: Create ACI Display Name Mapping Function
- Add `_get_aci_display_name(aci: int | None) -> str` function in `excel_writer.py`
- Implement mapping logic:
  - None -> "True Color" (24-bit RGB, no ACI index)
  - 0 -> "ByBlock"
  - 1 -> "Red"
  - 2 -> "Yellow"
  - 3 -> "Green"
  - 4 -> "Cyan"
  - 5 -> "Blue"
  - 6 -> "Magenta"
  - 7 -> "White"
  - 8-255 -> "Color {aci}"
  - 256 -> "ByLayer"
- Add docstring with examples

### Step 6: Update _create_color_analysis_sheet()
- Import `EXCEL_COLUMN_COLOR_AUTOCAD_NAME` constant
- Add new column after `EXCEL_COLUMN_COLOR_SAMPLE` in DataFrame construction
- Map ACI values to display names using `_get_aci_display_name()`
- Update empty DataFrame column list for consistency

### Step 7: Update _format_color_analysis_sheet()
- Adjust column widths for new 9-column layout (A-I instead of A-H)
- Add width for new column G (color_autocad_name): 20 characters
- Shift existing column references:
  - Old column G (color_entity_type) becomes column H
  - Old column H (color_entity_count) becomes column I
- Update right-alignment for numeric columns (now C, D, E, I)

### Step 8: Write Unit Tests for ACI Extraction
- Add tests in `test_extractor.py` for `_resolve_entity_color_with_aci()`
- Test ACI values for ByBlock (0), named colors (1-7), numbered colors (8-255), ByLayer (256)
- Test True Color entities return None for ACI (use `true_color_test.dxf` fixture)
- Test that `color_aci` field is present in all `ColorAnalysisRecord` entries

### Step 9: Write Unit Tests for ACI Display Name Mapping
- Add tests in `test_excel_writer.py` for `_get_aci_display_name()`
- Test all named colors (1-7)
- Test numbered colors (8, 30, 220, 255)
- Test special values (0 = ByBlock, 256 = ByLayer)
- Test None returns "True Color"

### Step 10: Write Unit Tests for Excel Output
- Add tests in `test_excel_writer.py` to verify new column appears in output
- Verify column header is "Color Autocad Name" (formatted from snake_case)
- Verify column position is after "Color Sample"
- Verify correct values for various ACI indices

### Step 11: Write Unit Tests for Formatting
- Add tests in `test_excel_formatting.py` for updated column layout
- Verify column G width is set correctly
- Verify column positions are correct after shift

### Step 12: Run Validation Commands
- Execute all validation commands to ensure zero regressions

## Testing Strategy
### Unit Tests
- `_resolve_entity_color_with_aci()`: Test RGB and ACI extraction for all color types
- `_get_aci_display_name()`: Test all ACI value mappings (0, 1-7, 8-255, 256)
- `_create_color_analysis_sheet()`: Test new column inclusion and correct values
- `ColorAnalysisRecord`: Test that all records include `color_aci` field

### Integration Tests
- Full extraction pipeline: Verify ACI values flow from DXF through to Excel output
- Excel file verification: Load generated Excel and verify column exists with correct data

### Edge Cases
- ByBlock color (ACI 0): Should display "ByBlock"
- ByLayer color (ACI 256): Should display "ByLayer"
- Boundary colors: ACI 7 (White), ACI 8 (first numbered), ACI 255 (last numbered)
- True Color (ACI None): Should display "True Color"
- Mixed color sources: Drawing with ByLayer, ByBlock, named, numbered, and True Colors

### Playwright MCP Tests
Not applicable - this feature is backend Excel generation only, no UI changes.

## Acceptance Criteria
- [ ] New column "Color Autocad Name" appears in Color Analysis sheet
- [ ] Column appears after "Color Sample" column (column G)
- [ ] ACI 1-7 display named colors: Red, Yellow, Green, Cyan, Blue, Magenta, White
- [ ] ACI 8-255 display as "Color N" format (e.g., "Color 30", "Color 220")
- [ ] ACI 0 displays "ByBlock"
- [ ] ACI 256 displays "ByLayer"
- [ ] True Color entities (ACI None) display "True Color"
- [ ] All existing tests pass
- [ ] New tests cover all ACI mappings including True Color
- [ ] Column width is appropriate for content

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests including new ACI tests
- `uv run pytest app/tests/core/test_excel_writer.py -v` - Run Excel writer tests including new column tests
- `uv run pytest app/tests/core/test_excel_formatting.py -v` - Run formatting tests including updated layout
- `uv run pytest app/tests/ -v` - Run complete test suite for full regression check
- `uv run mypy app/` - Verify type safety with new TypedDict field
- `uv run ruff check app/` - Check for linting issues

## Notes
- The ACI (AutoCAD Color Index) is a standard 256-color palette used by AutoCAD since early versions
- Colors 1-7 are the "primary" colors with official names; colors 8-255 are referred to by number
- ByBlock (0) means the entity inherits color from its parent block; ByLayer (256) means it inherits from its layer
- True Color (24-bit RGB) entities bypass the ACI palette entirely; these return `None` for ACI and display as "True Color"
- The existing `_resolve_entity_color_to_rgb()` already handles True Color via `entity.dxf.true_color` (added in spec 006)
- The ezdxf library provides `aci2rgb()` for converting ACI to RGB, but not the reverse; we track ACI during extraction
- The existing `_resolve_entity_color_to_rgb()` function already handles the ACI resolution logic; we're extending it to preserve the ACI value
