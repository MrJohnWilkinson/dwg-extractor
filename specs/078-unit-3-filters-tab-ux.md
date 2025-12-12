# Feature: Filters Tab UX Improvements

## Feature Description
Improve the Filters tab user experience in the Advanced Settings window with two enhancements:
1. **Styled Info Banner**: Replace the plain text info label with a visually distinct banner containing an "i" indicator and subtle background color, making the informational message more prominent and professional
2. **Real-Time Validation**: Replace FocusOut-based validation with trace_add-based validation so users see validation feedback (red border on invalid input) immediately as they type, rather than only when leaving the field

This is Unit 3 of the settings synchronization plan (Steps 7-8 from plan 075), following:
- Unit 1 (commit 700cad8): Bidirectional settings sync between main GUI and Advanced Settings
- Unit 2 (commit 29777db): UI button/window polish (button renames, minsize constraint)

## User Story
As a DXF Block Extractor user
I want clear visual feedback when viewing filter settings and entering values
So that I understand the Filters tab is read-only and catch input errors immediately

## Problem Statement
The current Filters tab has two UX issues:
1. **Plain info label**: The message explaining that filter settings are controlled from the main window is displayed as plain gray text that can be easily overlooked, causing user confusion about why values aren't editable
2. **Delayed validation feedback**: Entry fields only validate on FocusOut, meaning users don't see validation errors until they click elsewhere. This delays error discovery and creates a confusing experience when invalid values persist

## Solution Statement
Implement two targeted improvements:
1. **Styled Info Banner**: Create a CTkFrame with a subtle background color containing an "i" indicator label and the info text, making the message visually prominent and consistent with modern UI patterns
2. **Real-Time Validation**: Replace the FocusOut event binding with trace_add("write", ...) on the entry's StringVar, triggering validation on every keystroke for immediate visual feedback

## Relevant Files
Use these files to implement the feature:

- **`app/core/settings_window.py`** - Advanced Settings window containing:
  - `_populate_filters_tab()` method (lines 534-634) - needs styled info banner replacement
  - `_create_setting_row()` method (lines 189-351) - needs trace_add validation replacement
  - `_validate_entry()` method (lines 407-474) - validation logic (no changes needed, already works with trace_add)

- **`app/tests/core/test_settings.py`** - Existing settings tests for reference on test patterns

## Implementation Plan

### Phase 1: Foundation
Understand the current implementation of the info label in `_populate_filters_tab()` and the FocusOut binding in `_create_setting_row()`. Both changes are independent and can be implemented in any order.

### Phase 2: Core Implementation
1. Replace the plain info label with a styled CTkFrame containing an "i" indicator and formatted text
2. Replace FocusOut binding with trace_add callback for real-time validation

### Phase 3: Integration
Both changes integrate seamlessly with existing functionality:
- The styled banner replaces existing content, no new behavior
- trace_add validation calls the same `_validate_entry()` method, just triggered differently

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Replace Plain Info Label with Styled Banner in Filters Tab

Update `_populate_filters_tab()` in `app/core/settings_window.py`:

- Remove the plain `info_label` CTkLabel (lines 544-552)
- Add a styled CTkFrame with distinct background color
- Add an "i" indicator label inside the frame
- Add the info text label inside the frame with improved formatting

**Location:** Lines 543-552 in `app/core/settings_window.py`

**Current code:**
```python
# Info label - filters are controlled from main window
info_label = ctk.CTkLabel(
    scroll_frame,
    text="Note: Filter settings are controlled from the main window. "
    "This tab shows current values for reference.",
    font=ctk.CTkFont(size=10),
    text_color="gray",
    wraplength=550,
)
info_label.pack(anchor="w", pady=(0, 10))
```

**Updated code:**
```python
# PROMINENT INFO BANNER - styled frame with info indicator
info_frame = ctk.CTkFrame(
    scroll_frame,
    fg_color=("gray85", "gray25"),  # Subtle but distinct background
    corner_radius=8,
)
info_frame.pack(fill="x", pady=(0, 15), padx=5)

# Info icon/indicator
info_indicator = ctk.CTkLabel(
    info_frame,
    text="i",
    font=ctk.CTkFont(size=14, weight="bold"),
    text_color=("gray40", "gray70"),
    width=24,
)
info_indicator.pack(side="left", padx=(12, 8), pady=10)

# Info text
info_label = ctk.CTkLabel(
    info_frame,
    text="Filter settings are configured in the main window.\n"
    "This tab displays current values for reference only.",
    font=ctk.CTkFont(size=11),
    text_color=("gray30", "gray80"),
    anchor="w",
    justify="left",
)
info_label.pack(side="left", fill="x", expand=True, pady=10, padx=(0, 12))
```

### Step 2: Replace FocusOut Binding with trace_add for Real-Time Validation

Update `_create_setting_row()` in `app/core/settings_window.py`:

- Remove the FocusOut event binding
- Add trace_add callback on the StringVar to trigger validation on every write

**Location:** Lines 323-340 in `app/core/settings_window.py`

**Current code:**
```python
var = ctk.StringVar(
    value=str(current_value) if current_value is not None else ""
)
entry = ctk.CTkEntry(
    control_frame,
    width=100,
    textvariable=var,
)
entry.pack()
entry.var = var

# Bind validation on focus out
entry.bind(
    "<FocusOut>",
    lambda e, k=setting_key, w=entry: self._validate_entry(k, w),
)

self._entry_widgets[setting_key] = entry
```

**Updated code:**
```python
var = ctk.StringVar(
    value=str(current_value) if current_value is not None else ""
)
entry = ctk.CTkEntry(
    control_frame,
    width=100,
    textvariable=var,
)
entry.pack()
entry.var = var

# Real-time validation using trace_add (replaces FocusOut binding)
var.trace_add(
    "write",
    lambda *_, k=setting_key, w=entry: self._validate_entry(k, w),
)

self._entry_widgets[setting_key] = entry
```

### Step 3: Run Validation Commands

Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
No new unit tests required for this feature:
- The styled info banner is purely visual UI change
- The trace_add validation uses the same `_validate_entry()` method which is already tested
- Both changes are cosmetic/behavioral improvements to existing functionality

### Integration Tests
Not applicable - these are self-contained UI improvements within the settings window.

### Edge Cases
For the real-time validation:
- Empty field (should clear error, restore normal border)
- Partial input like "3." while typing "3.5" (may show error briefly, then clear when complete)
- Invalid input like "abc" (should show red border immediately)
- Very large numbers (should validate against max_value constraints)
- Negative numbers (should validate against min_value constraints)

### Playwright MCP Tests
Not applicable - these UI improvements require manual visual verification. The functionality (validation behavior) is unchanged, only the trigger timing differs.

## Acceptance Criteria

1. **Info banner has distinct background**: The info banner displays with a subtle gray background that makes it stand out from other content
2. **Info indicator displays correctly**: An "i" character displays in bold on the left side of the banner
3. **Info text is readable**: The info text is properly formatted with two lines and readable in both light and dark modes
4. **Real-time validation triggers**: Typing an invalid value in any numeric entry field (Performance, Precision tabs) shows a red border immediately
5. **Valid input restores normal border**: Typing a valid value after invalid input restores the normal gray border immediately
6. **Validation works for all entry fields**: All numeric entry fields in Performance and Precision tabs use real-time validation
7. **Empty field is handled**: Clearing an entry field removes any validation error styling
8. **All existing tests pass**: No regressions in existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run settings sync tests (from Unit 1)
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check all code
- `uv run ruff check app/` - Lint all code
- `uv run ruff format app/ --check` - Verify formatting

## Testing Checklist (Manual)

These changes require manual testing on a system with a display server:

- [ ] Verify info banner has distinct background color in Filters tab
- [ ] Verify info indicator "i" displays correctly on the left side
- [ ] Verify info text is readable in light mode
- [ ] Verify info text is readable in dark mode
- [ ] Type invalid value in "Polygon Count Threshold", verify red border appears immediately
- [ ] Type valid value, verify border returns to normal immediately
- [ ] Type invalid value in "Arc Flattening Sagitta", verify red border appears immediately
- [ ] Type valid value, verify border returns to normal immediately
- [ ] Verify validation works for all numeric entry fields in Performance tab
- [ ] Verify validation works for all numeric entry fields in Precision tab
- [ ] Clear an entry field, verify no error styling remains

## Notes

### Implementation Order
The steps are ordered for clean implementation:
1. Style the info banner first (Step 1) as it's a self-contained visual change
2. Replace validation binding (Step 2) as it's independent of Step 1
3. Run validation (Step 3) to ensure no regressions

### GUI Testing Limitation
Per README.md: "Skip GUI tests in WSL - X server issues make it unreliable." These UI changes require manual testing on a system with a display server. The automated tests verify no regressions in existing functionality.

### Color Tuples for Theme Support
The color tuples like `("gray85", "gray25")` follow customtkinter convention:
- First value is for light mode
- Second value is for dark mode
This ensures the banner looks appropriate in both appearance modes.

### trace_add vs FocusOut Behavior
- **FocusOut**: Only triggers when user clicks outside the field, leaving the field
- **trace_add("write")**: Triggers on every change to the StringVar (every keystroke)

The trade-off is that trace_add may briefly show errors on partial input (e.g., "3." while typing "3.5"), but this is preferred UX as users get immediate feedback and the error clears as soon as input is valid.

### Prior Unit Context
This is Unit 3 of the settings synchronization plan:
- Unit 1 (spec 076, commit 700cad8): Added bidirectional settings sync, `_sync_numeric_setting()`, `_refresh_from_settings()`, trace_add callbacks
- Unit 2 (spec 077, commit 29777db): Renamed buttons ("Advanced Settings", "Apply All Changes", "Save All as Default"), added minsize(650, 600) constraint
