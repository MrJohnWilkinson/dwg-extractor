# Feature: HATCH Entity Support in Color Analysis

## Feature Description
Add HATCH entity extraction to the Color Analysis sheet, allowing CAD analysts to see hatch counts grouped by color and layer. This extends the existing color analysis functionality (which currently supports LINE, LWPOLYLINE, POLYLINE, TEXT, and MTEXT) to include HATCH entities as a geometric entity type, aggregated similarly to Lines and Polylines.

## User Story
As a CAD analyst
I want hatches included in Color Analysis
So that I can see hatch counts by color/layer

## Problem Statement
Currently, the Color Analysis extraction in `extract_color_analysis()` only processes LINE, LWPOLYLINE, POLYLINE, TEXT, and MTEXT entities. HATCH entities, which are commonly used in CAD drawings for area fills and patterns, are excluded from analysis. This limits the completeness of the color analysis report for drawings that make significant use of hatches.

## Solution Statement
Extend the `extract_color_analysis()` function to include HATCH entities as a geometric entity type. HATCHes will be aggregated by color + layer combination (similar to Lines and Polylines) and displayed with entity type "Hatches" (plural, consistent with existing naming convention). This requires minimal changes: adding "HATCH" to the entity type filter, adding an elif branch for HATCH processing, and updating documentation to reflect the new capability.

## Relevant Files
Use these files to implement the feature:

- `app/core/extractor.py` - Contains `extract_color_analysis()` function where HATCH support needs to be added at line 263 (entity type filter) and new elif branch for HATCH processing
- `app/core/types.py` - Contains `ColorAnalysisRecord` TypedDict docstring that needs to be updated to include HATCH
- `app/tests/core/test_extractor.py` - Contains test classes `TestExtractor` and `TestColorAnalysis` where new HATCH tests will be added

### New Files
- `app/tests/assets/create_hatch_test.py` - Script to create test DXF file with HATCH entities
- `app/tests/assets/hatch_test.dxf` - Test fixture DXF file with various HATCH entities for testing

## Implementation Plan
### Phase 1: Foundation
- Update the `ColorAnalysisRecord` docstring in `app/core/types.py` to include HATCH as a supported entity type
- Create test fixture creation script for HATCH entities

### Phase 2: Core Implementation
- Add "HATCH" to the entity type filter at `extractor.py:263`
- Add elif branch for HATCH processing using the `geometric_entities` dictionary pattern (like LINE/POLYLINE)
- Use grouping key `(color_r, color_g, color_b, color_aci, layer_name, "Hatches")` for aggregation

### Phase 3: Integration
- Create test DXF file with HATCH entities using the creation script
- Add unit tests to verify HATCH extraction and aggregation
- Validate the feature works end-to-end with existing color analysis flow

## Step by Step Tasks

### Step 1: Update ColorAnalysisRecord docstring
- Open `app/core/types.py`
- Update the `ColorAnalysisRecord` class docstring to include HATCH in the description
- Change entity_type description from `'Lines', 'Polylines', 'TEXT', or 'MTEXT'` to `'Lines', 'Polylines', 'Hatches', 'TEXT', or 'MTEXT'`

### Step 2: Add HATCH to entity type filter
- Open `app/core/extractor.py`
- Locate line 263 where entity type filtering occurs
- Add "HATCH" to the tuple: `if entity_type not in ("LINE", "LWPOLYLINE", "POLYLINE", "HATCH", "TEXT", "MTEXT"):`

### Step 3: Add HATCH processing branch
- In `extract_color_analysis()` function, add elif branch after POLYLINE handling (around line 286)
- Use pattern matching existing geometric entity handling:
```python
elif entity_type == "HATCH":
    key = (color_r, color_g, color_b, color_aci, layer_name, "Hatches")
    geometric_entities[key] = geometric_entities.get(key, 0) + 1
```

### Step 4: Update extract_color_analysis docstring
- Update the function docstring to mention HATCH entities in the description
- Update the entity_type field description to include "Hatches"

### Step 5: Create test fixture creation script
- Create `app/tests/assets/create_hatch_test.py`
- Script should create DXF file with:
  - HATCH entities with different ACI colors on different layers
  - HATCH entities with True Color
  - Multiple hatches with same color/layer (to test aggregation)
  - Mix of HATCH with other entity types for integration testing

### Step 6: Generate test DXF file
- Run the creation script to generate `app/tests/assets/hatch_test.dxf`

### Step 7: Add unit tests for HATCH extraction
- Add new test class or tests to `TestColorAnalysis` in `app/tests/core/test_extractor.py`:
  - `test_color_analysis_extracts_hatch_entities` - verify HATCHes are extracted
  - `test_color_analysis_hatch_aggregation` - verify same color/layer hatches are grouped
  - `test_color_analysis_hatch_entity_type_name` - verify entity_type is "Hatches" (plural)
  - `test_color_analysis_hatch_with_true_color` - verify True Color hatches work
  - `test_color_analysis_hatch_mixed_entities` - verify HATCHes work alongside Lines/Polylines/Text

### Step 8: Run validation commands
- Run type checking, linting, and tests to validate implementation

## Testing Strategy
### Unit Tests
- Test that HATCH entities are recognized and processed by `extract_color_analysis()`
- Test that multiple HATCH entities with same color+layer are aggregated correctly
- Test that entity_type field is "Hatches" (plural form)
- Test that HATCH True Color extraction works correctly
- Test that HATCH works with ByLayer and ByBlock colors

### Integration Tests
- Test complete extraction pipeline with DXF containing mixed entity types (HATCH + LINE + POLYLINE + TEXT)
- Verify HATCH records appear correctly sorted in color_analysis_data

### Edge Cases
- HATCH with no fill color (may not resolve to RGB)
- HATCH on non-existent layer
- Empty drawing with only HATCH entities
- HATCH with ByBlock color (should default to white as per existing behavior)

### Playwright MCP Tests
- Not applicable - this is a backend data extraction feature with no GUI changes

## Acceptance Criteria
- HATCH entities appear in color_analysis_data with entity_type="Hatches"
- HATCH entities are grouped by (color_r, color_g, color_b, color_aci, layer_name, "Hatches")
- Entity count reflects aggregation of multiple hatches with same color/layer
- annotation_contents is empty string for HATCH (consistent with geometric entities)
- True Color HATCH entities have color_aci=None
- ACI color HATCH entities have correct color_aci value
- All existing tests continue to pass
- Type checking passes with no errors
- Linting passes with no errors

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to validate no type errors
- `uv run ruff check app/` - Run linting to validate code style
- `uv run pytest app/tests/core/test_extractor.py -v` - Run extractor tests including new HATCH tests
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions

## Notes
- HATCH entities in DXF can have complex boundary paths, but for color analysis we only need the color and layer properties which are standard entity attributes
- The ezdxf library handles HATCH entities as first-class entities with standard dxf attributes (color, layer, rgb)
- Using "Hatches" (plural) as the entity_type value maintains consistency with existing naming convention ("Lines", "Polylines")
- No new library dependencies required - ezdxf already supports HATCH entity type
