# Feature: Unit 5 - Settings Window Pre/Post-Filters Subsections

## Feature Description

This unit updates the Settings Window's Filters tab (`app/core/settings_window.py`) to organize filter settings into logical Pre-Filters and Post-Filters subsections. The current implementation displays all filter settings as a flat list without visual grouping. This update adds:

1. **Pre-Filters Subsection** - A labeled group containing:
   - Skip Curved Entities (read-only display)
   - Min Line Length Filter enabled/amount (read-only display)

2. **Post-Filters Subsection** - A labeled group containing:
   - Existing filters (Precision Fix, Gap Bridge, Min Area, Min Side)
   - New Curved Lines Filter (read-only display)

3. **Unit Override** - Displayed standalone at the bottom as it applies to both filter types

The subsections use bold labels with descriptive text to help users understand when each filter type is applied (before vs after polygon detection).

## User Story

As a DXF Block Extractor user
I want to see filter settings organized into Pre-Filters and Post-Filters subsections in the Settings Window
So that I can quickly understand which filters run before polygon detection (to reduce processing) versus after detection (to validate shapes)

## Problem Statement

The current Settings Window Filters tab displays all filter settings in a single flat list. With the addition of new pre-filter settings (Skip Curved Entities, Min Line Length Filter) and post-filter settings (Curved Lines Filter) in Units 1-4, users need visual organization to understand:
- Which filters reduce processing load by running before polygon detection
- Which filters validate shapes by running after polygon detection

The flat list makes it difficult to understand the filter execution order and purpose.

## Solution Statement

Update the `_populate_filters_tab()` method in `app/core/settings_window.py` to:

1. Add a "Pre-Filters" subsection header with description text explaining its purpose
2. Display the three pre-filter settings (skip_curved_entities, min_line_length_filter_enabled, min_line_length_filter_amount) under this subsection
3. Add a "Post-Filters" subsection header with description text explaining its purpose
4. Display all existing post-filter settings plus the new curved_filter_enabled under this subsection
5. Move unit_override to the end as a standalone setting (applies to both filter types)

All settings remain read-only as they are configured in the main window.

## Relevant Files

Use these files to implement the feature:

- **`app/core/settings_window.py`** - Main file to modify. Contains `_populate_filters_tab()` method (lines 544-663) that needs restructuring. The `_create_setting_row()` helper method (lines 191-354) is already implemented and will be reused.
- **`app/core/settings.py`** - Reference for SETTINGS_SECTIONS showing the filter keys (lines 52-69). Contains the setting keys that must be displayed: skip_curved_entities, min_line_length_filter_enabled, min_line_length_filter_amount, curved_filter_enabled.
- **`app/core/constants.py`** - Reference for the new filter constants (lines 313-340) to verify setting keys exist.

## Implementation Plan

### Phase 1: Foundation

No foundation changes required. All necessary infrastructure exists:
- `_create_setting_row()` helper method is implemented
- New filter settings are registered in SETTINGS_VALIDATION_REGISTRY (Unit 1)
- Settings are synced from main window (Unit 4)

### Phase 2: Core Implementation

Restructure `_populate_filters_tab()` to:
1. Keep existing scrollable frame and section header
2. Keep existing info banner
3. Add Pre-Filters subsection with label and description
4. Add three pre-filter setting rows
5. Add Post-Filters subsection with label and description
6. Reorder existing filter rows under Post-Filters
7. Add new curved_filter_enabled row
8. Move unit_override to standalone position at end

### Phase 3: Integration

No additional integration required. The Settings Window already:
- Reads settings from SettingsManager via `_create_setting_row()`
- Refreshes on tab switch via `_refresh_tab()`
- Updates Summary tab via `_refresh_summary()`

## Step by Step Tasks

### Step 1: Update `_populate_filters_tab()` Method Structure

Replace the entire `_populate_filters_tab()` method in `app/core/settings_window.py` (lines 544-663) with the new implementation that organizes settings into subsections.

The new structure should be:
1. Scrollable frame (existing)
2. Section header (existing)
3. Info banner (existing)
4. Pre-Filters subsection label and description
5. Pre-filter setting rows (3 settings)
6. Post-Filters subsection label and description
7. Post-filter setting rows (8 existing settings + 1 new)
8. Unit override (standalone at end)

### Step 2: Add Pre-Filters Subsection

After the info banner, add:

```python
        # PRE-FILTERS subsection
        prefilter_label = ctk.CTkLabel(
            scroll_frame,
            text="Pre-Filters",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        prefilter_label.pack(anchor="w", pady=(10, 5))

        prefilter_desc = ctk.CTkLabel(
            scroll_frame,
            text="Applied before polygon detection to reduce processing",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        prefilter_desc.pack(anchor="w", pady=(0, 10))
```

### Step 3: Add Pre-Filter Setting Rows

Add the three pre-filter setting rows after the Pre-Filters subsection header:

```python
        self._create_setting_row(
            scroll_frame,
            "skip_curved_entities",
            "Skip Curved Entities",
            "Excludes CIRCLE and ARC entities from edge extraction. "
            "Reduces polygon detection workload for drawings with many curves.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_line_length_filter_enabled",
            "Min Line Length Filter",
            "Filters out LINE entities shorter than the threshold. "
            "Useful for removing small detail lines.",
            readonly=True,
        )

        self._create_setting_row(
            scroll_frame,
            "min_line_length_filter_amount",
            "Min Line Length Amount",
            "Minimum LINE entity length in drawing units. "
            "Lines shorter than this are excluded.",
            readonly=True,
        )
```

### Step 4: Add Post-Filters Subsection

After the pre-filter setting rows, add:

```python
        # POST-FILTERS subsection
        postfilter_label = ctk.CTkLabel(
            scroll_frame,
            text="Post-Filters",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        postfilter_label.pack(anchor="w", pady=(15, 5))

        postfilter_desc = ctk.CTkLabel(
            scroll_frame,
            text="Applied after polygon detection to validate shapes",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        postfilter_desc.pack(anchor="w", pady=(0, 10))
```

### Step 5: Add Post-Filter Setting Rows

Add the existing post-filter setting rows (precision_fix, gap_bridge, min_area, min_side) followed by the new curved_filter_enabled row:

```python
        # Existing post-filter rows (precision_fix, gap_bridge, min_area, min_side)
        # ... (keep existing code for 8 setting rows) ...

        # New curved filter row
        self._create_setting_row(
            scroll_frame,
            "curved_filter_enabled",
            "Curved Lines Filter",
            "Excludes polygons containing curved edges (arcs, circles). "
            "Useful for focusing on rectangular shapes only.",
            readonly=True,
        )
```

### Step 6: Add Standalone Unit Override

Move unit_override to the end as a standalone setting:

```python
        # Unit override (standalone - applies to both filter types)
        self._create_setting_row(
            scroll_frame,
            "unit_override",
            "Unit Override",
            "Manual unit override for drawing interpretation. "
            "None means auto-detect from DXF file.",
            readonly=True,
        )
```

### Step 7: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests

No new unit tests required. The Settings Window changes are UI-only and:
- Use existing `_create_setting_row()` helper that is already tested
- Display read-only values from SettingsManager that is already tested
- Don't introduce new logic or state management

### Integration Tests

The existing settings sync tests (`test_main_settings_sync.py`) already verify:
- Pre-filter settings sync correctly (from Unit 4)
- Post-filter settings sync correctly (from Unit 4)
- Settings persist across save/load cycles

### Edge Cases

- Settings with None values display as "Not set" (handled by existing `_create_setting_row()`)
- Boolean settings display as "True"/"False" (handled by existing logic)
- Numeric settings display as string representation (handled by existing logic)

### Playwright MCP Tests

Not applicable for this unit. Per README guidance, GUI tests are skipped in WSL due to X server issues. The Settings Window is a modal dialog that would require GUI automation to test properly.

## Acceptance Criteria

1. Filters tab displays "Pre-Filters" subsection header with bold text
2. Filters tab displays pre-filter description text in gray
3. Filters tab displays three pre-filter settings (skip_curved_entities, min_line_length_filter_enabled, min_line_length_filter_amount)
4. Filters tab displays "Post-Filters" subsection header with bold text
5. Filters tab displays post-filter description text in gray
6. Filters tab displays all existing post-filter settings (precision_fix, gap_bridge, min_area, min_side - 8 rows total)
7. Filters tab displays new curved_filter_enabled setting under Post-Filters
8. Filters tab displays unit_override as standalone setting at end
9. All filter settings remain read-only (configured in main window)
10. Reset Section button still works correctly for filters section
11. Summary tab still displays all filter settings correctly
12. `mypy app/` passes with no errors
13. `ruff check app/` passes with no errors
14. `pytest app/tests/` passes with all tests green

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run settings sync tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Notes

- **Visual Consistency**: The subsection labels use `size=12, weight="bold"` to differentiate from the section header (`size=14, weight="bold"`) while still being prominent.

- **Description Text**: Both subsection descriptions use `size=10, text_color="gray"` matching the existing pattern used elsewhere in the Settings Window.

- **Spacing**: The `pady` values are chosen to create visual grouping:
  - Pre-Filters label: `pady=(10, 5)` - space above to separate from info banner
  - Pre-Filters desc: `pady=(0, 10)` - space below before settings
  - Post-Filters label: `pady=(15, 5)` - larger space above to create visual separation
  - Post-Filters desc: `pady=(0, 10)` - space below before settings

- **Dependencies**: This unit depends on Units 1-4 being complete:
  - Unit 1: Constants, types, and settings registration
  - Unit 2: Pre-filter and post-filter logic in geometry.py
  - Unit 3: Parameter threading through extract_blocks() and _detect_content_zone()
  - Unit 4: Main GUI controls for all new filter settings

- **Future Consideration**: If more pre-filters or post-filters are added in the future, the subsection structure makes it easy to add new setting rows under the appropriate header.
