# Chore: GUI Testing Implementation

## Chore Description
Add automated GUI testing infrastructure to detect widget visibility and layout issues in the DWG Block Extractor application. The test suite will include fast introspection tests (no rendering) and GUI rendering tests (using Xvfb). This ensures widgets are properly created, configured, and added to layouts, preventing bugs where widgets exist in code but aren't visible to users.

## Relevant Files
Use these files to resolve the chore:

- **pyproject.toml** - Project configuration file where pytest-mock dependency will be added and pytest markers (fast, gui) will be configured under [tool.pytest.ini_options]
- **app/main.py** - GUI application entry point (lines 41-279) containing the DWGExtractorApp class with all widget creation logic in _create_widgets() method that needs test coverage
- **ai_docs/001-naming-convention-guide.md** - Python naming conventions guide that must be followed for all test function and variable names (snake_case, descriptive prefixes like test_, is_, has_, etc.)
- **README.md** - Project documentation that will be updated with new test commands for running fast and GUI tests

### New Files

- **app/tests/gui/__init__.py** - Package initializer for GUI test module (empty file)
- **app/tests/gui/test_widget_structure.py** - Fast introspection tests that verify widgets exist, have correct attributes, parent relationships, and proper configuration without rendering
- **app/tests/gui/test_gui_rendering.py** - Rendering tests under Xvfb that verify widgets are visible, properly packed/gridded, and display correct properties in the widget tree

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add pytest-mock dependency
- Run `uv add --dev pytest-mock` to add pytest-mock to dev dependencies in pyproject.toml
- This allows mocking of GUI components and file dialogs in tests

### Step 2: Configure pytest markers
- Edit pyproject.toml to add pytest markers configuration under [tool.pytest.ini_options]
- Add `markers` list with two entries:
  - `fast: Fast tests that don't require GUI rendering (introspection only)`
  - `gui: GUI rendering tests that require Xvfb display server`
- Update coverage configuration to include `app/main.py` in coverage tracking (add to coverage sources if not already included)

### Step 3: Create GUI test directory structure
- Create directory `app/tests/gui/`
- Create empty file `app/tests/gui/__init__.py`

### Step 4: Write introspection tests (test_widget_structure.py)
- Create `app/tests/gui/test_widget_structure.py`
- Mark all tests with `@pytest.mark.fast` decorator
- Follow naming conventions from ai_docs/001-naming-convention-guide.md
- Implement test class `TestWidgetStructure` with the following test methods:
  - `test_app_initializes_successfully` - Verify DWGExtractorApp() creates instance without errors
  - `test_window_has_correct_configuration` - Verify window title is "DWG Block Extractor", geometry is "500x300", resizable is False
  - `test_file_entry_widget_exists_with_correct_attributes` - Verify file_entry exists, width=360, placeholder text matches MSG_SELECT_FILE, state is readonly
  - `test_browse_button_exists_with_correct_attributes` - Verify browse_button exists, text="Browse", width=120, command is _browse_file
  - `test_extract_button_exists_with_correct_attributes` - Verify extract_button exists, text="Extract", width=120, command is _extract_blocks, initial state is disabled
  - `test_progress_bar_exists_with_correct_attributes` - Verify progress_bar exists, width=400, height=20, initial value is 0
  - `test_status_label_exists_with_correct_attributes` - Verify status_label exists, initial text is empty string
  - `test_extract_button_enables_after_file_selection` - Mock file selection, verify extract_button state becomes normal
  - `test_widgets_have_correct_parent_relationships` - Verify all widgets have proper parent frames
- Each test should create fresh DWGExtractorApp instance and destroy it in cleanup
- Use assertions with descriptive error messages

### Step 5: Write rendering tests (test_gui_rendering.py)
- Create `app/tests/gui/test_gui_rendering.py`
- Mark all tests with `@pytest.mark.gui` decorator
- Follow naming conventions from ai_docs/001-naming-convention-guide.md
- Implement test class `TestGUIRendering` with the following test methods:
  - `test_file_entry_is_visible_in_widget_tree` - Create app, call update_idletasks(), verify file_entry.winfo_ismapped() returns True
  - `test_browse_button_is_visible_in_widget_tree` - Verify browse_button.winfo_ismapped() returns True
  - `test_extract_button_is_visible_in_widget_tree` - Verify extract_button.winfo_ismapped() returns True
  - `test_progress_bar_is_visible_in_widget_tree` - Verify progress_bar.winfo_ismapped() returns True
  - `test_status_label_is_visible_in_widget_tree` - Verify status_label.winfo_ismapped() returns True
  - `test_widgets_fail_if_not_packed_or_gridded` - Create widget without pack() or grid(), verify winfo_ismapped() returns False (validates test methodology)
  - `test_all_widgets_have_proper_geometry` - Verify all widgets have non-zero width/height after rendering
- Add pytest fixture `gui_app` that:
  - Creates DWGExtractorApp instance
  - Calls update_idletasks() to force rendering
  - Yields app for test
  - Destroys app in cleanup
- Tests MUST fail if widgets are created but not added to layout (no .pack() or .grid() called)

### Step 6: Update README.md documentation
- Add new section under "## Usage" titled "### Testing"
- Document three test command options:
  - `uv run pytest app/tests/` - Run all tests (existing command, keep for backward compatibility)
  - `uv run pytest -m fast` - Run only fast introspection tests (no GUI rendering)
  - `xvfb-run uv run pytest -m gui` - Run GUI rendering tests under Xvfb virtual display
  - `uv run pytest --cov=app app/tests/` - Run tests with coverage including GUI code
- Add note: "WSL2 users should use `-m fast` to skip GUI rendering tests due to X server limitations"
- Update existing test commands to maintain consistency with root-relative path convention

### Step 7: Verify test coverage configuration
- Ensure pyproject.toml coverage configuration includes `app/main.py` in source paths
- Verify coverage excludes .venv, build, dist directories
- Test that coverage reports include GUI code when running `uv run pytest --cov=app app/tests/`

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest -m fast -v` - Run fast introspection tests, verify all widget structure tests pass
- `xvfb-run uv run pytest -m gui -v` - Run GUI rendering tests under Xvfb, verify all visibility tests pass
- `uv run pytest app/tests/core/ -v` - Run existing core tests to ensure no regressions
- `uv run pytest --cov=app app/tests/ --cov-report=term-missing` - Run full test suite with coverage, verify app/main.py is included in coverage report
- `uv run mypy app/` - Type check all code including new test files
- `uv run ruff check app/` - Lint all code including new test files

## Notes

### Test Philosophy
- **Fast tests** (@pytest.mark.fast) - No GUI rendering required, test object attributes and relationships via introspection. Fast feedback for CI/CD.
- **GUI tests** (@pytest.mark.gui) - Require Xvfb, test actual rendering and visibility. Slower but catch layout bugs.
- Both test types complement each other: introspection tests verify widgets exist with correct config, rendering tests verify they're visible to users.

### Critical Validation Requirement
Tests MUST fail when widgets are created but not added to layout. The test in `test_widgets_fail_if_not_packed_or_gridded` validates this by creating an unpacked widget and asserting winfo_ismapped() returns False. This ensures our test methodology catches real layout bugs.

### WSL2 Considerations
- Xvfb is already installed on the system per prerequisites
- WSL2 X server can be unreliable (per README.md line 78)
- Fast tests provide value on WSL2 without X server dependencies
- GUI tests should be run on systems with proper X display or in CI with Xvfb

### Naming Convention Compliance
All test functions and variables must follow ai_docs/001-naming-convention-guide.md:
- Test functions: `test_<descriptive_name_with_underscores>`
- Boolean checks: `is_visible`, `has_correct_width`
- Variables: `gui_app`, `file_entry_widget`, `browse_button_state`
- Avoid abbreviations except standard ones (app, gui, config)

### Coverage Integration
Adding app/main.py to coverage tracking enables measurement of GUI code coverage, previously excluded from coverage reports. This helps identify untested GUI paths and increases overall project coverage beyond the current 98% core module coverage.
