# Chore: UI Button/Window Polish

## Chore Description
UI polish for settings buttons and window constraints. This chore implements three changes to improve clarity and usability:
1. Rename the "Settings" button to "Advanced Settings" in the main window with appropriate width adjustment
2. Rename the Apply/Save buttons in the Advanced Settings window to "Apply All Changes" and "Save All as Default" for better scope clarity
3. Add `minsize(650, 600)` constraint to the Advanced Settings window to prevent it from being resized too small

This is Unit 2 of the settings synchronization plan (Steps 4-6 from plan 075), following Unit 1 which implemented settings sync core functionality.

## Relevant Files
Use these files to resolve the chore:

- **`app/main.py`** - Main GUI application containing the Settings button that needs renaming:
  - Lines 200-207: Settings button definition with `text="Settings"` and `width=80`
  - The button command `_open_advanced_settings()` already has the correct name

- **`app/core/settings_window.py`** - Advanced Settings window containing:
  - Lines 91-94: Window configuration including `geometry("650x600")` and `resizable(True, True)` - needs `minsize()` addition
  - Lines 162-186: Button frame with Apply, Cancel, and Save as Default buttons that need renaming

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Rename Settings Button to "Advanced Settings" in Main Window

Update the Settings button in `app/main.py`:

- Change `text="Settings"` to `text="Advanced Settings"`
- Change `width=80` to `width=120` to accommodate the longer text

**Location:** Lines 200-207 in `app/main.py`

**Current code:**
```python
# Settings button
self.settings_button = ctk.CTkButton(
    button_frame,
    text="Settings",
    width=80,
    command=self._open_advanced_settings,
)
self.settings_button.pack(side="left", padx=(10, 0))
```

**Updated code:**
```python
# Settings button
self.settings_button = ctk.CTkButton(
    button_frame,
    text="Advanced Settings",
    width=120,
    command=self._open_advanced_settings,
)
self.settings_button.pack(side="left", padx=(10, 0))
```

### Step 2: Add minsize Constraint to Advanced Settings Window

Update the window configuration in `app/core/settings_window.py`:

- Add `self.minsize(650, 600)` after `self.resizable(True, True)`
- This prevents the window from being shrunk smaller than its initial size

**Location:** Lines 91-94 in `app/core/settings_window.py`

**Current code:**
```python
# Configure window
self.title("Advanced Settings")
self.geometry("650x600")
self.resizable(True, True)
```

**Updated code:**
```python
# Configure window
self.title("Advanced Settings")
self.geometry("650x600")
self.resizable(True, True)
self.minsize(650, 600)  # Prevent window from being too small
```

### Step 3: Rename "Save as Default" Button to "Save All as Default"

Update the Save as Default button in `app/core/settings_window.py`:

- Change `text="Save as Default"` to `text="Save All as Default"`
- Change `width=120` to `width=140` to accommodate the longer text
- Also update the confirmation text in `_on_save_as_default()` method

**Location:** Lines 162-169 in `app/core/settings_window.py`

**Current code:**
```python
# Left side - Save as Default
self.save_default_button = ctk.CTkButton(
    button_frame,
    text="Save as Default",
    width=120,
    command=self._on_save_as_default,
)
self.save_default_button.pack(side="left")
```

**Updated code:**
```python
# Left side - Save as Default
self.save_default_button = ctk.CTkButton(
    button_frame,
    text="Save All as Default",
    width=140,
    command=self._on_save_as_default,
)
self.save_default_button.pack(side="left")
```

### Step 4: Update Button Confirmation Text in Save Handler

Update the confirmation text in `_on_save_as_default()` method to match the new button label:

**Location:** Lines 978-980 in `app/core/settings_window.py`

**Current code:**
```python
# Show brief confirmation
self.save_default_button.configure(text="Saved!")
self.after(
    1500, lambda: self.save_default_button.configure(text="Save as Default")
)
```

**Updated code:**
```python
# Show brief confirmation
self.save_default_button.configure(text="Saved!")
self.after(
    1500, lambda: self.save_default_button.configure(text="Save All as Default")
)
```

### Step 5: Rename "Apply" Button to "Apply All Changes"

Update the Apply button in `app/core/settings_window.py`:

- Change `text="Apply"` to `text="Apply All Changes"`
- Change `width=100` to `width=130` to accommodate the longer text

**Location:** Lines 171-178 in `app/core/settings_window.py`

**Current code:**
```python
# Right side - Cancel and Apply
self.apply_button = ctk.CTkButton(
    button_frame,
    text="Apply",
    width=100,
    command=self._on_apply,
)
self.apply_button.pack(side="right")
```

**Updated code:**
```python
# Right side - Cancel and Apply
self.apply_button = ctk.CTkButton(
    button_frame,
    text="Apply All Changes",
    width=130,
    command=self._on_apply,
)
self.apply_button.pack(side="right")
```

### Step 6: Run Validation Commands

Execute all validation commands to ensure the chore is complete with zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_settings.py -v` - Run settings tests
- `uv run pytest app/tests/core/test_main_settings_sync.py -v` - Run settings sync tests (from Unit 1)
- `uv run pytest app/tests/ -v` - Run full test suite to ensure no regressions
- `uv run mypy app/` - Type check all code
- `uv run ruff check app/` - Lint all code
- `uv run ruff format app/ --check` - Verify formatting

## Testing Checklist

Manual testing is required for these UI changes:

- [ ] Verify "Advanced Settings" button displays correctly in main window
- [ ] Verify button width (120px) accommodates "Advanced Settings" text without truncation
- [ ] Verify "Apply All Changes" button displays correctly in Advanced Settings window
- [ ] Verify "Save All as Default" button displays correctly in Advanced Settings window
- [ ] Verify button widths (130px, 140px) accommodate new text without truncation
- [ ] Verify "Saved!" confirmation shows, then reverts to "Save All as Default"
- [ ] Verify Advanced Settings window cannot be resized smaller than 650x600
- [ ] Verify Advanced Settings window can still be maximized/expanded
- [ ] Verify window maintains functionality after resize constraints applied

## Notes

### Implementation Order
The steps are ordered for clean implementation:
1. Rename main window button first (Step 1) as it's independent
2. Add window constraints (Step 2) before button changes in settings window
3. Rename Save button (Steps 3-4) including confirmation text update
4. Rename Apply button (Step 5) last
5. Validation (Step 6) ensures no regressions

### GUI Testing Limitation
Per README.md: "Skip GUI tests in WSL - X server issues make it unreliable." These UI changes require manual testing on a system with a display server. The automated tests verify no regressions in existing functionality.

### Button Width Considerations
- "Settings" (8 chars) -> "Advanced Settings" (17 chars): width 80 -> 120 (+40px)
- "Apply" (5 chars) -> "Apply All Changes" (17 chars): width 100 -> 130 (+30px)
- "Save as Default" (15 chars) -> "Save All as Default" (19 chars): width 120 -> 140 (+20px)

The width increases are conservative estimates to ensure text fits with padding.

### Prior Unit Context
This is Unit 2 of the settings synchronization plan. Unit 1 (spec 076) added:
- `_sync_numeric_setting()` helper method
- `_refresh_from_settings()` method
- `trace_add` callbacks for instant sync
- Tests in `app/tests/core/test_main_settings_sync.py`

Unit 1 was completed successfully with commit 700cad8.
