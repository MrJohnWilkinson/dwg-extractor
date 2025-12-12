# Feature: Unit 4 - Main GUI Pre-Filters Section and Curved Lines Filter

## Feature Description

This unit adds the GUI controls in the main window (`app/main.py`) for the new dual-stage filter system. It implements:

1. **Pre-Filters Section** - A new labeled section in the main window containing:
   - Skip Curved Entities checkbox (excludes CIRCLE and ARC entities from edge extraction)
   - Min Line Length Filter checkbox with amount entry (excludes short LINE entities)

2. **Filters Section Reorganization** - The existing filters (Precision Fix, Gap Bridge, Min Area, Min Side) are grouped under a new "FILTERS" header to distinguish them as post-filters

3. **Curved Lines Filter** - A new post-filter checkbox (excludes polygons containing curved edges after detection)

4. **Extraction Integration** - All new filter settings are wired through to the `extract_blocks()` function call

This unit builds on Units 1-3 which established the constants, types, settings, core filtering logic, and parameter threading through the extraction pipeline.

## User Story

As a DXF Block Extractor user
I want to control pre-filter and post-filter settings from the main window
So that I can reduce processing time by excluding curved entities and short lines before polygon detection, and filter out curved polygons after detection

## Problem Statement

The current main window GUI only exposes post-filter controls (Precision Fix, Gap Bridge, Min Area, Min Side). Users have no way to:
- Skip curved entities (circles, arcs) during edge extraction to reduce processing overhead
- Filter out short line segments that create noise in polygon detection
- Exclude polygons with curved edges from content zone results

The filter settings added in Units 1-3 are not accessible through the GUI, limiting their usefulness.

## Solution Statement

Add GUI controls to the main window that:
1. Display a labeled "PRE-FILTERS" section with hint text explaining its purpose
2. Provide Skip Curved Entities checkbox (simple toggle, no amount)
3. Provide Min Line Length Filter checkbox with disabled/enabled amount entry
4. Display a labeled "FILTERS" section header for existing post-filters
5. Add Curved Lines Filter checkbox in the post-filters section
6. Wire all new settings through `_sync_settings_to_manager()` and `_extraction_worker()`

The implementation follows the established patterns from existing filter controls (Min Area, Min Side) and maintains consistency with the main window's visual style.

## Relevant Files

Use these files to implement the feature:

- **`app/main.py`** - Main GUI window. Lines 86-139 contain existing filter instance variables. Lines 147-486 contain `_create_widgets()`. Lines 565-720 contain `_extraction_worker()`. Lines 1166-1200 contain `_sync_settings_to_manager()`. Lines 940-966 contain toggle handlers for existing filters.
- **`app/core/constants.py`** - Contains default values for the new settings (lines 313-340): `DEFAULT_SKIP_CURVED_ENTITIES`, `DEFAULT_MIN_LINE_LENGTH_FILTER_ENABLED`, `DEFAULT_MIN_LINE_LENGTH_FILTER`, `DEFAULT_CURVED_FILTER_ENABLED`
- **`app/core/settings.py`** - SettingsManager used for persistence. New settings already registered in Unit 1.
- **`app/core/extractor.py`** - Contains `extract_blocks()` with the new filter parameters added in Unit 3 (lines 975-1010): `skip_curved_entities`, `min_line_length_filter_enabled`, `min_line_length_filter_amount`, `curved_filter_enabled`
- **`app/tests/core/test_main_settings_sync.py`** - Tests for settings synchronization. Will need updates for new filter settings.

## Implementation Plan

### Phase 1: Instance Variables

Add instance variables for the new filter settings after existing filter vars in `__init__()`. These bind to the GUI widgets and sync with SettingsManager.

### Phase 2: Pre-Filters Section UI

Add the "PRE-FILTERS" section with header, hint, separator, and two filter rows:
- Skip Curved Entities (checkbox only)
- Min Line Length Filter (checkbox + amount entry)

Then add the "FILTERS" section header before the existing filter controls.

### Phase 3: Curved Lines Filter UI

Add the Curved Lines Filter checkbox row after the Min Side Filter section.

### Phase 4: Toggle Handlers

Add toggle handler methods for the new filters that sync settings to manager.

### Phase 5: Settings Sync

Update `_sync_settings_to_manager()` to include the new filter settings.

### Phase 6: Extraction Worker

Update `_extraction_worker()` to read the new filter values and pass them to `extract_blocks()`.

### Phase 7: Testing

Update the settings sync tests to verify the new filter settings are synced correctly.

## Step by Step Tasks

### Step 1: Add Pre-Filter Instance Variables in `__init__()`

In `app/main.py`, add after the Min Side Filter settings (around line 108, after `self.min_side_filter_amount_var`):

```python
        # Pre-Filter settings
        self.skip_curved_entities_var = ctk.BooleanVar(
            value=self.settings.get("skip_curved_entities")
        )
        self.min_line_length_filter_var = ctk.BooleanVar(
            value=self.settings.get("min_line_length_filter_enabled")
        )
        self.min_line_length_filter_amount_var = ctk.StringVar(
            value=str(self.settings.get("min_line_length_filter_amount") or "")
        )
```

### Step 2: Add Curved Filter Instance Variable

Add after the Pre-Filter settings:

```python
        # Curved Lines Filter setting (post-filter)
        self.curved_filter_var = ctk.BooleanVar(
            value=self.settings.get("curved_filter_enabled")
        )
```

### Step 3: Add Trace Callback for Min Line Length Amount

Add a trace callback for instant sync of the min line length amount (after the existing trace callbacks around line 139):

```python
        self.min_line_length_filter_amount_var.trace_add(
            "write",
            lambda *_: self._sync_numeric_setting(
                "min_line_length_filter_amount", self.min_line_length_filter_amount_var
            ),
        )
```

### Step 4: Add Pre-Filters Section Header in `_create_widgets()`

In `_create_widgets()`, add after the Units row frame (around line 250, after `units_hint.pack(side="left")`):

```python
        # Pre-Filters section header
        prefilter_header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        prefilter_header_frame.pack(fill="x", pady=(10, 5))

        prefilter_label = ctk.CTkLabel(
            prefilter_header_frame,
            text="PRE-FILTERS",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        prefilter_label.pack(side="left")

        prefilter_hint = ctk.CTkLabel(
            prefilter_header_frame,
            text="(reduces processing before polygon detection)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        prefilter_hint.pack(side="left", padx=(10, 0))

        # Pre-filter separator
        prefilter_sep = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray40")
        prefilter_sep.pack(fill="x", pady=(0, 10))
```

### Step 5: Add Skip Curved Entities Checkbox

Add after the pre-filter separator:

```python
        # Skip Curved Entities checkbox
        skip_curved_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        skip_curved_frame.pack(pady=(5, 10))

        self.skip_curved_checkbox = ctk.CTkCheckBox(
            skip_curved_frame,
            text="Skip Curved Entities",
            variable=self.skip_curved_entities_var,
            command=self._on_skip_curved_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.skip_curved_checkbox.pack(side="left", padx=(0, 10))

        skip_curved_hint = ctk.CTkLabel(
            skip_curved_frame,
            text="(excludes circles and arcs)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        skip_curved_hint.pack(side="left")

        # Separator
        separator_prefilter1 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator_prefilter1.pack(fill="x", pady=5)
```

### Step 6: Add Min Line Length Filter Row

Add after the prefilter1 separator:

```python
        # Min Line Length Filter row
        min_line_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        min_line_frame.pack(pady=(5, 10))

        self.min_line_length_checkbox = ctk.CTkCheckBox(
            min_line_frame,
            text="Min Line Length Filter",
            variable=self.min_line_length_filter_var,
            command=self._on_min_line_length_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.min_line_length_checkbox.pack(side="left", padx=(0, 10))

        min_line_amount_label = ctk.CTkLabel(
            min_line_frame,
            text="Amount:",
            font=ctk.CTkFont(size=12),
        )
        min_line_amount_label.pack(side="left", padx=(0, 5))

        self.min_line_length_entry = ctk.CTkEntry(
            min_line_frame,
            width=80,
            textvariable=self.min_line_length_filter_amount_var,
            state="disabled",
        )
        self.min_line_length_entry.pack(side="left")
```

### Step 7: Add Filters Section Header

Add after the Min Line Length Filter row:

```python
        # Filters section header (post-filters)
        filter_header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        filter_header_frame.pack(fill="x", pady=(15, 5))

        filter_label = ctk.CTkLabel(
            filter_header_frame,
            text="FILTERS",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        filter_label.pack(side="left")

        filter_hint = ctk.CTkLabel(
            filter_header_frame,
            text="(validates shapes after polygon detection)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        filter_hint.pack(side="left", padx=(10, 0))

        filter_sep = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray40")
        filter_sep.pack(fill="x", pady=(0, 10))
```

### Step 8: Add Curved Lines Filter Row

Add after the Min Side Filter section (around line 382, before the progress bar):

```python
        # Fifth separator
        separator5 = ctk.CTkFrame(self.main_frame, height=1, fg_color="gray50")
        separator5.pack(fill="x", pady=5)

        # Curved Lines Filter row
        curved_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        curved_frame.pack(pady=(5, 10))

        self.curved_filter_checkbox = ctk.CTkCheckBox(
            curved_frame,
            text="Curved Lines Filter",
            variable=self.curved_filter_var,
            command=self._on_curved_filter_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.curved_filter_checkbox.pack(side="left", padx=(0, 10))

        curved_hint = ctk.CTkLabel(
            curved_frame,
            text="(excludes polygons with curved edges)",
            font=ctk.CTkFont(size=10),
            text_color="gray",
        )
        curved_hint.pack(side="left")
```

### Step 9: Add Entry State Sync for Min Line Length in Widget Init

At the end of `_create_widgets()`, after the existing entry state syncs (around line 486), add:

```python
        if self.min_line_length_filter_var.get():
            self.min_line_length_entry.configure(state="normal")
        # min_line_length_entry is already disabled by default
```

### Step 10: Add Toggle Handler Methods

Add after `_on_min_side_filter_toggle()` (around line 966):

```python
    def _on_skip_curved_toggle(self) -> None:
        """Handle skip curved entities checkbox toggle."""
        self._sync_settings_to_manager()

    def _on_min_line_length_toggle(self) -> None:
        """Handle min line length filter checkbox toggle."""
        enabled = self.min_line_length_filter_var.get()
        state = "normal" if enabled else "disabled"
        self.min_line_length_entry.configure(state=state)
        self._sync_settings_to_manager()

    def _on_curved_filter_toggle(self) -> None:
        """Handle curved filter checkbox toggle."""
        self._sync_settings_to_manager()
```

### Step 11: Update `_sync_settings_to_manager()` for Pre-Filters

In `_sync_settings_to_manager()`, add after the existing min_side_filter_amount sync (around line 1187):

```python
        # Pre-Filters
        self.settings.set("skip_curved_entities", self.skip_curved_entities_var.get())
        self.settings.set(
            "min_line_length_filter_enabled", self.min_line_length_filter_var.get()
        )
        self._sync_numeric_setting(
            "min_line_length_filter_amount", self.min_line_length_filter_amount_var
        )
```

### Step 12: Update `_sync_settings_to_manager()` for Curved Filter

Add after the pre-filters sync:

```python
        # Post-Filters (curved)
        self.settings.set("curved_filter_enabled", self.curved_filter_var.get())
```

### Step 13: Update `_extraction_worker()` to Read New Filter Values

In `_extraction_worker()`, add after the existing filter settings retrieval (around line 619, after min_side_filter_amount):

```python
            # Pre-Filters
            skip_curved_entities = self.skip_curved_entities_var.get()
            min_line_length_filter_enabled = self.min_line_length_filter_var.get()
            min_line_length_filter_amount = None
            if min_line_length_filter_enabled:
                try:
                    min_line_length_filter_amount = float(
                        self.min_line_length_filter_amount_var.get()
                    )
                except ValueError:
                    pass

            # Post-Filters
            curved_filter_enabled = self.curved_filter_var.get()
```

### Step 14: Update `_extraction_worker()` Logger Info

Update the logger.info call to include the new filter settings (around line 626):

```python
            self.logger.info(
                f"Extraction settings: unit_override={unit_override}, "
                f"gap_bridge_enabled={gap_bridge_enabled}, "
                f"gap_bridge_amount={gap_bridge_amount}, "
                f"precision_fix_enabled={precision_fix_enabled}, "
                f"precision_fix_amount={precision_fix_amount}, "
                f"min_area_filter_enabled={min_area_filter_enabled}, "
                f"min_area_filter_amount={min_area_filter_amount}, "
                f"min_side_filter_enabled={min_side_filter_enabled}, "
                f"min_side_filter_amount={min_side_filter_amount}, "
                f"skip_curved_entities={skip_curved_entities}, "
                f"min_line_length_filter_enabled={min_line_length_filter_enabled}, "
                f"min_line_length_filter_amount={min_line_length_filter_amount}, "
                f"curved_filter_enabled={curved_filter_enabled}"
            )
```

### Step 15: Update `extract_blocks()` Call with New Parameters

Update the `extract_blocks()` call in `_extraction_worker()` to include the new parameters (around line 648):

```python
            extraction_result = extract_blocks(
                self.selected_file_path,
                self.abort_event,
                unit_override=unit_override,
                gap_bridge_enabled=gap_bridge_enabled,
                gap_bridge_amount=gap_bridge_amount,
                precision_fix_enabled=precision_fix_enabled,
                precision_fix_amount=precision_fix_amount,
                min_area_filter_enabled=min_area_filter_enabled,
                min_area_filter_amount=min_area_filter_amount,
                min_side_filter_enabled=min_side_filter_enabled,
                min_side_filter_amount=min_side_filter_amount,
                skip_curved_entities=skip_curved_entities,
                min_line_length_filter_enabled=min_line_length_filter_enabled,
                min_line_length_filter_amount=min_line_length_filter_amount,
                curved_filter_enabled=curved_filter_enabled,
                polygon_count_threshold=polygon_threshold,
                line_segment_threshold=line_threshold,
                entity_count_threshold=entity_threshold,
            )
```

### Step 16: Add Tests for New Filter Settings Sync

Add new test class to `app/tests/core/test_main_settings_sync.py`:

```python
class TestPreFilterSettingsSync:
    """Tests for pre-filter and curved filter settings synchronization."""

    def test_syncs_skip_curved_entities(self, settings_manager: SettingsManager) -> None:
        """Verify skip_curved_entities boolean is synced."""
        settings_manager.set("skip_curved_entities", True)
        assert settings_manager.get("skip_curved_entities") is True

        settings_manager.set("skip_curved_entities", False)
        assert settings_manager.get("skip_curved_entities") is False

    def test_syncs_min_line_length_filter_enabled(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify min_line_length_filter_enabled boolean is synced."""
        settings_manager.set("min_line_length_filter_enabled", True)
        assert settings_manager.get("min_line_length_filter_enabled") is True

        settings_manager.set("min_line_length_filter_enabled", False)
        assert settings_manager.get("min_line_length_filter_enabled") is False

    def test_syncs_min_line_length_filter_amount(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify min_line_length_filter_amount is synced."""
        settings_manager.set("min_line_length_filter_amount", 1.5)
        assert settings_manager.get("min_line_length_filter_amount") == 1.5

    def test_syncs_curved_filter_enabled(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify curved_filter_enabled boolean is synced."""
        settings_manager.set("curved_filter_enabled", True)
        assert settings_manager.get("curved_filter_enabled") is True

        settings_manager.set("curved_filter_enabled", False)
        assert settings_manager.get("curved_filter_enabled") is False

    def test_min_line_length_filter_amount_validates_range(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify min_line_length_filter_amount respects validation range."""
        # Valid value
        result = settings_manager.set("min_line_length_filter_amount", 50.0)
        assert result is True
        assert settings_manager.get("min_line_length_filter_amount") == 50.0

        # Value above max (100.0) should be rejected
        result = settings_manager.set("min_line_length_filter_amount", 150.0)
        assert result is False

    def test_new_filter_settings_persist(self, tmp_path: Path) -> None:
        """Verify new filter settings persist across save/load cycle."""
        config_path = tmp_path / "settings.json"

        # First session: set and save
        manager1 = SettingsManager(config_path=config_path)
        manager1.set("skip_curved_entities", True)
        manager1.set("min_line_length_filter_enabled", True)
        manager1.set("min_line_length_filter_amount", 2.5)
        manager1.set("curved_filter_enabled", True)
        manager1.save()

        # Second session: load and verify
        manager2 = SettingsManager(config_path=config_path)
        manager2.load()

        assert manager2.get("skip_curved_entities") is True
        assert manager2.get("min_line_length_filter_enabled") is True
        assert manager2.get("min_line_length_filter_amount") == 2.5
        assert manager2.get("curved_filter_enabled") is True
```

### Step 17: Run Validation Commands

Execute all validation commands to ensure zero regressions.

## Testing Strategy

### Unit Tests

- Test that skip_curved_entities boolean syncs correctly
- Test that min_line_length_filter_enabled boolean syncs correctly
- Test that min_line_length_filter_amount numeric value syncs correctly
- Test that curved_filter_enabled boolean syncs correctly
- Test that min_line_length_filter_amount respects validation range (0.0-100.0)
- Test that new filter settings persist across save/load cycle

### Integration Tests

- The `_extraction_worker()` changes are tested implicitly through the existing extractor tests
- The parameter threading was validated in Unit 3

### Edge Cases

- Empty string in min_line_length_filter_amount_var should not raise
- Invalid string (e.g., "abc") in min_line_length_filter_amount_var should not raise
- Filter disabled with amount set should not pass amount to extract_blocks()

### Playwright MCP Tests

- Not applicable for this unit (GUI changes are difficult to test in WSL per README guidance)

## Acceptance Criteria

1. Main window displays "PRE-FILTERS" section with header and hint text
2. Skip Curved Entities checkbox toggles correctly and syncs to SettingsManager
3. Min Line Length Filter checkbox enables/disables the amount entry
4. Min Line Length Filter amount entry syncs to SettingsManager
5. Main window displays "FILTERS" section header before existing post-filters
6. Curved Lines Filter checkbox toggles correctly and syncs to SettingsManager
7. All new filter settings are passed to `extract_blocks()` during extraction
8. New filter settings persist across application restarts
9. All existing tests pass without modification
10. `mypy app/` passes with no errors
11. `ruff check app/` passes with no errors
12. `pytest app/tests/` passes with all tests green

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify type definitions are correct
- `uv run ruff check app/` - Run linting to verify code style compliance
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run settings sync tests including new filter tests
- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests
- `uv run pytest app/tests/ -v` - Run full test suite to verify zero regressions

## Notes

- **Window Height**: The main window geometry is set to 600x750. Adding the new PRE-FILTERS section and Curved Lines Filter row may require adjusting this. Monitor if scrolling becomes necessary.

- **Widget Naming Convention**: The new widgets follow the established naming pattern:
  - Instance variables: `self.<feature>_var` for BooleanVar/StringVar
  - Checkboxes: `self.<feature>_checkbox`
  - Entry widgets: `self.<feature>_entry`

- **Toggle Handler Pattern**: The new toggle handlers follow the same pattern as `_on_min_area_filter_toggle()`:
  - Enable/disable related entry widget based on checkbox state
  - Call `_sync_settings_to_manager()` to persist changes

- **Settings Sync Pattern**: Pre-filter and post-filter settings are synced using the same pattern as existing filters:
  - Boolean flags via `self.settings.set(key, var.get())`
  - Numeric amounts via `self._sync_numeric_setting()`

- **Extraction Worker Pattern**: The new filter values are read from instance variables and passed to `extract_blocks()` using keyword arguments, consistent with existing filter parameters.

- **Dependencies**: This unit depends on Units 1-3 being complete:
  - Unit 1: Constants, types, and settings registration
  - Unit 2: Pre-filter and post-filter logic in geometry.py
  - Unit 3: Parameter threading through extract_blocks() and _detect_content_zone()
