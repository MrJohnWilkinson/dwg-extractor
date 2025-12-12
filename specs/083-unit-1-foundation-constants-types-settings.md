# Feature: Unit 1 - Foundation for Dual-Stage Filter (Constants, Types, Settings)

## Feature Description

This unit adds the foundational infrastructure for the dual-stage filter feature by introducing constants, types, and settings section entries for 3 new filters:

1. **Pre-Filter 1: Skip Curved Entities** (boolean) - Excludes CIRCLE and ARC entities from edge extraction
2. **Pre-Filter 2: Min Line Length Filter** (boolean + float amount) - Excludes LINE entities below a length threshold
3. **Post-Filter: Curved Lines Filter** (boolean) - Excludes polygons containing curved edges after detection

This foundation enables subsequent units to implement the actual filtering logic by providing:
- Default values and validation constraints in the constants module
- Type definitions in the AppSettings TypedDict
- Settings section registration for persistence and reset functionality

## User Story

As a DXF Block Extractor user
I want the application to support new pre-filter and post-filter settings
So that subsequent features can add filtering controls to reduce processing time and improve polygon detection accuracy

## Problem Statement

The current filter system only supports post-filters (applied after polygon detection). Complex DXF drawings with many curved entities (circles, arcs) or short line segments cause excessive processing time in the unary_union and polygonize operations. Adding pre-filters that reduce input before these expensive operations requires foundational type and constant definitions.

## Solution Statement

Add constants, types, and settings section entries for 3 new filters without implementing the actual filtering logic. This follows the established pattern used by existing filters (precision_fix, gap_bridge, min_area, min_side) and prepares the codebase for the implementation in subsequent units.

## Relevant Files

Use these files to implement the feature:

- **`app/core/constants.py`** - Add new filter constants (defaults, min/max values) and SETTINGS_VALIDATION_REGISTRY entries. Lines 293-422 contain existing filter constants and registry.
- **`app/core/types.py`** - Add new filter settings to AppSettings TypedDict. Lines 274-322 contain the existing TypedDict definition.
- **`app/core/settings.py`** - Add new filter settings to SETTINGS_SECTIONS["filters"] list. Lines 52-63 contain the current filters section.
- **`app/tests/core/test_constants.py`** - Add tests for new constants and validation registry entries.
- **`app/tests/core/test_settings.py`** - Update test for settings sections coverage.

## Implementation Plan

### Phase 1: Foundation (This Unit)

Add constants, types, and settings section entries for the 3 new filters. This establishes the type-safe foundation that the Settings Manager uses for validation and persistence.

### Phase 2: Core Implementation (Future Units)

Implement the actual pre-filter logic in `_extract_all_edges()` and post-filter logic as `_polygon_has_curved_edges()` function in geometry.py.

### Phase 3: Integration (Future Units)

Wire the filter parameters through extractor.py, main.py GUI, and settings_window.py.

## Step by Step Tasks

### Step 1: Add Constants to `app/core/constants.py`

Add after line 311 (after `MIN_SIDE_FILTER_MAX`):

- Add `DEFAULT_SKIP_CURVED_ENTITIES: bool = False` with docstring
- Add `DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED: bool = False` with docstring
- Add `DEFAULT_MIN_LINE_LENGTH_FILTER: float = 0.5` with docstring
- Add `MIN_LINE_LENGTH_FILTER_MIN: float = 0.0` with docstring
- Add `MIN_LINE_LENGTH_FILTER_MAX: float = 100.0` with docstring
- Add `DEFAULT_CURVED_FILTER_ENABLED: bool = False` with docstring
- Add `CURVED_FILTER_TOLERANCE: float = 0.01` with docstring

### Step 2: Add Validation Registry Entries to `app/core/constants.py`

Add to `SETTINGS_VALIDATION_REGISTRY` after the `min_side_filter_amount` entry:

- Add `"skip_curved_entities"` entry with min_value=None, max_value=None, default=False, unit_aware=False
- Add `"min_line_length_filter_enabled"` entry with min_value=None, max_value=None, default=False, unit_aware=False
- Add `"min_line_length_filter_amount"` entry with min_value=0.0, max_value=100.0, default=0.5, unit_aware=False
- Add `"curved_filter_enabled"` entry with min_value=None, max_value=None, default=False, unit_aware=False

### Step 3: Add Types to `app/core/types.py`

Add to `AppSettings` TypedDict after `min_side_filter_amount` (~line 298):

- Add `skip_curved_entities: bool` with Pre-Filters comment
- Add `min_line_length_filter_enabled: bool`
- Add `min_line_length_filter_amount: float | None`
- Add `curved_filter_enabled: bool` with Post-Filters comment

### Step 4: Update Settings Section in `app/core/settings.py`

Update `SETTINGS_SECTIONS["filters"]` list to include new settings in the appropriate order:

```python
"filters": [
    "unit_override",
    # Pre-Filters
    "skip_curved_entities",
    "min_line_length_filter_enabled",
    "min_line_length_filter_amount",
    # Post-Filters (existing + new)
    "precision_fix_enabled",
    "precision_fix_amount",
    "gap_bridge_enabled",
    "gap_bridge_amount",
    "min_area_filter_enabled",
    "min_area_filter_amount",
    "min_side_filter_enabled",
    "min_side_filter_amount",
    "curved_filter_enabled",
],
```

### Step 5: Add Tests for New Constants

Add new test class `TestPreFilterConstants` to `app/tests/core/test_constants.py`:

- Test `DEFAULT_SKIP_CURVED_ENTITIES` is False
- Test `DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED` is False
- Test `DEFAULT_MIN_LINE_LENGTH_FILTER` is 0.5
- Test `MIN_LINE_LENGTH_FILTER_MIN` is 0.0
- Test `MIN_LINE_LENGTH_FILTER_MAX` is 100.0
- Test `MIN_LINE_LENGTH_FILTER_MIN < MIN_LINE_LENGTH_FILTER_MAX`

Add new test class `TestCurvedFilterConstants`:

- Test `DEFAULT_CURVED_FILTER_ENABLED` is False
- Test `CURVED_FILTER_TOLERANCE` is 0.01
- Test `CURVED_FILTER_TOLERANCE` is in reasonable range (0.001 to 1.0)

### Step 6: Update Registry Tests

Update `TestSettingsValidationRegistry` in `app/tests/core/test_constants.py`:

- Update `test_registry_has_all_settings` expected count from 25 to 29
- Add new filter settings to expected_settings list
- Verify new entries have all required keys

### Step 7: Update Settings Section Test

Update `test_settings_sections_covers_all_settings` in `app/tests/core/test_settings.py`:

- Test should automatically pass since it compares SETTINGS_SECTIONS to SETTINGS_VALIDATION_REGISTRY

### Step 8: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests

- Test that all new constants have expected default values
- Test that MIN/MAX constraints are valid (MIN < MAX)
- Test that validation registry entries have all required keys
- Test that new settings are included in the "filters" section
- Test that SETTINGS_SECTIONS covers all SETTINGS_VALIDATION_REGISTRY keys

### Integration Tests

- Not applicable for this unit (foundation only)

### Edge Cases

- Verify MIN_LINE_LENGTH_FILTER_MIN allows 0.0 (disabled state)
- Verify CURVED_FILTER_TOLERANCE is small but not zero

### Playwright MCP Tests

- Not applicable for this unit (no GUI changes)

## Acceptance Criteria

1. `constants.py` contains all 7 new constants with correct values and docstrings
2. `SETTINGS_VALIDATION_REGISTRY` contains 4 new entries with correct validation metadata
3. `AppSettings` TypedDict contains 4 new fields with correct types
4. `SETTINGS_SECTIONS["filters"]` contains all 4 new setting keys in the specified order
5. All existing tests pass without modification
6. New tests verify constant values and registry completeness
7. `mypy app/` passes with no errors
8. `ruff check app/` passes with no errors
9. `pytest app/tests/` passes with all tests green

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests including new filter tests
- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests including sections coverage
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Notes

- **Default Values**: All new filters default to disabled (False) to preserve existing behavior
- **Unit Awareness**: `min_line_length_filter_amount` is NOT unit-aware (uses absolute drawing units) unlike `min_area_filter_amount` and `min_side_filter_amount` which have unit-specific defaults
- **Ordering**: Pre-filters appear before post-filters in the SETTINGS_SECTIONS list for logical grouping
- **Future Implementation**: This unit only adds infrastructure; actual filtering logic will be added in subsequent units (geometry.py, extractor.py, main.py, settings_window.py)
- **Registry Count**: After this change, SETTINGS_VALIDATION_REGISTRY will have 29 entries (was 25)
