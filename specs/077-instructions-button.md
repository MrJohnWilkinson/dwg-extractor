# Feature: Instructions Button

## Feature Description
Add an "Instructions" button to the main application window that displays a popup with step-by-step guidance on how to properly export DWG files to DXF format using the WBLOCK method. This helps users understand the recommended workflow for preparing their CAD files before using the extractor.

## User Story
As a user
I want an "Instructions" button in the application
So that I can quickly see how to properly export DWG files to DXF format using the WBLOCK method

## Problem Statement
Users may not know the optimal way to export DWG files to DXF format. The standard "Save As DXF" method in AutoCAD can sometimes lose block definitions, particularly those with zero insertions. Users need accessible guidance within the application on using the WBLOCK command for complete block preservation.

## Solution Statement
Add an "Instructions" button to the existing button row (after "Advanced Settings") that displays a standard message dialog containing step-by-step WBLOCK export instructions. The button follows the existing UI patterns - hidden during extraction and restored afterward.

## Relevant Files
Use these files to implement the feature:

- `app/main.py` - Main GUI application file where the button will be added. Contains `_create_widgets()` for UI creation, `_start_extraction()` for hiding buttons during processing, and `_restore_ui()` for restoring buttons after extraction completes.

## Implementation Plan
### Phase 1: Foundation
No foundation work required - this feature uses existing patterns and components already in the codebase (ctk.CTkButton, messagebox.showinfo).

### Phase 2: Core Implementation
1. Create the Instructions button in `_create_widgets()` after the Settings button
2. Create a `_show_instructions()` method that displays the WBLOCK instructions via `messagebox.showinfo()`

### Phase 3: Integration
1. Add the Instructions button to `_start_extraction()` so it's hidden during file processing
2. Add the Instructions button to `_restore_ui()` so it's restored after extraction completes

## Step by Step Tasks

### Step 1: Add Instructions Button to UI
- In `app/main.py`, locate the `_create_widgets()` method
- Find where `self.settings_button` is created (around line 224-230)
- After the settings button creation, add the Instructions button:
  ```python
  # Instructions button
  self.instructions_button = ctk.CTkButton(
      button_frame,
      text="Instructions",
      width=120,
      command=self._show_instructions,
  )
  self.instructions_button.pack(side="left", padx=(10, 0))
  ```

### Step 2: Create the _show_instructions Method
- Add a new method `_show_instructions()` to the `DXFExtractorApp` class
- Use `messagebox.showinfo()` to display the instructions
- Content should include:
  - Title: "DWG to DXF Export Instructions"
  - Body: Step-by-step WBLOCK instructions and explanation of why WBLOCK is preferred

### Step 3: Hide Button During Extraction
- In the `_start_extraction()` method (around line 690)
- Add `self.instructions_button.pack_forget()` after the other button hide calls
- This ensures the button is hidden during file extraction

### Step 4: Restore Button After Extraction
- In the `_restore_ui()` method (around line 734)
- Add `self.instructions_button.pack(side="left", padx=(10, 0))` after the settings button restore
- This ensures the button reappears when extraction completes or is aborted

### Step 5: Run Validation Commands
- Run type checking: `uv run mypy app/`
- Run linting: `uv run ruff check app/`
- Run tests: `uv run pytest app/tests/`

## Testing Strategy
### Unit Tests
No unit tests required - this is a simple UI feature using standard tkinter messagebox which is difficult to unit test and provides minimal value.

### Integration Tests
Manual verification:
- Verify button appears in the button row after "Advanced Settings"
- Verify clicking button shows the instructions dialog
- Verify dialog can be closed
- Verify button is hidden during extraction
- Verify button reappears after extraction completes or is aborted

### Edge Cases
- Button visibility during extraction abort
- Button visibility after extraction error
- Dialog displays correctly on different screen sizes

### Playwright MCP Tests
Not applicable - this is a desktop application using customtkinter, not a web application.

## Acceptance Criteria
- [ ] Instructions button appears in the button row after "Advanced Settings" button
- [ ] Clicking the button displays a dialog with WBLOCK export instructions
- [ ] Dialog title is "DWG to DXF Export Instructions"
- [ ] Dialog content includes numbered steps for WBLOCK export
- [ ] Dialog content explains why WBLOCK is preferred over Save As
- [ ] Button is hidden during file extraction (matches existing button behavior)
- [ ] Button is restored after extraction completes or is aborted
- [ ] No type errors from mypy
- [ ] No linting errors from ruff
- [ ] All existing tests pass

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to ensure no type errors
- `uv run ruff check app/` - Run linting to ensure code style compliance
- `uv run pytest app/tests/` - Run all tests to ensure no regressions

## Notes
- The instructions content is based on the WBLOCK method which exports ALL block definitions, including those with zero insertions
- Standard "Save As DXF" can sometimes lose blocks, which is why WBLOCK is the recommended approach
- The button width (120) matches existing buttons for visual consistency
- Using `messagebox.showinfo()` is consistent with the existing `_show_success_ui()` and `_show_error_ui()` methods
