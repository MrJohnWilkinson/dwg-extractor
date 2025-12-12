# Feature: Data Models and Default Values Registry (Unit 3 - Phases B1-B2)

## Feature Description

This specification covers the foundational data structures for the GUI Settings infrastructure. It implements phases B1-B2 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md):

- **B1**: Add `AppSettings` and `SettingValidation` TypedDicts to `app/core/types.py`
- **B2**: Add default value constants and `SETTINGS_VALIDATION_REGISTRY` to `app/core/constants.py`

These TypedDicts and constants provide the type-safe foundation that the SettingsManager class (B3) and Advanced Settings Window (C2) will build upon.

**Scope:** B1-B2 only (data models and constants)

**Out of Scope (handled in later units):**
- B3: SettingsManager class implementation
- B4: Platform-specific config paths
- C1-C2: GUI integration
- D1-D2: Pipeline integration

**Prerequisites:**
- Unit 1 (A1-A3) completed: Parallel processing removed from extractor.py
- Unit 2 (A4-A6) completed: BlockAnalysisResult TypedDict deleted from types.py, tests updated

**Implementation Learnings from Previous Units:**
- Unit 1: Removed 92 lines of code from extractor.py, sequential processing in place
- Unit 2: Deleted BlockAnalysisResult TypedDict (18 lines), types.py now at 271 lines
- Tests: 856 passing

## User Story

As a developer implementing the GUI Settings infrastructure
I want type-safe data structures and centralized default values
So that I can build a robust, validated settings system with IDE support and compile-time checking

## Problem Statement

The application needs a comprehensive settings system to expose 24+ configurable options through an Advanced Settings modal. Currently:

1. Settings are scattered across multiple files without type definitions
2. Default values are hardcoded in various locations
3. No validation metadata exists for settings ranges
4. No TypedDict structure for type-safe settings access

## Solution Statement

Create two TypedDicts (`AppSettings` and `SettingValidation`) in types.py and a comprehensive set of default constants plus a `SETTINGS_VALIDATION_REGISTRY` dictionary in constants.py. This provides:

1. Type-safe settings dictionary with IDE autocompletion
2. Centralized default values for all 24 settings
3. Min/max validation ranges for numeric settings
4. Validation metadata registry mapping setting names to their constraints

## Relevant Files

Use these files to implement the feature:

- `app/core/types.py` - Add `AppSettings` and `SettingValidation` TypedDicts
  - Current line count: 271 lines
  - Last TypedDict ends at line 271 (BlockDefinitionRecord)
  - New TypedDicts will be added after BlockDefinitionRecord

- `app/core/constants.py` - Add default value constants and SETTINGS_VALIDATION_REGISTRY
  - Current line count: 304 lines
  - Already contains some defaults (GAP_BRIDGE_MIN/MAX, PRECISION_FIX_MIN/MAX, etc.)
  - New constants will be added at end of file
  - SETTINGS_VALIDATION_REGISTRY will reference existing and new constants

- `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md` - Reference document containing the exact field definitions for AppSettings and constants to add

- `app/tests/core/test_constants.py` - Add tests for new constants

## Implementation Plan

### Phase 1: Foundation (B1 - Data Models)

Add TypedDict definitions to `app/core/types.py`:

1. `AppSettings` TypedDict with `total=False` (all fields optional)
   - 24 fields organized by category: Filters, Performance, Precision, Output, Logging
   - Uses union types for optional values (e.g., `int | None`)

2. `SettingValidation` TypedDict for validation metadata
   - `min_value`: Lower bound for numeric settings
   - `max_value`: Upper bound for numeric settings
   - `default`: Default value for the setting
   - `unit_aware`: Whether default varies by drawing unit

### Phase 2: Core Implementation (B2 - Default Values Registry)

Add constants to `app/core/constants.py`:

1. **Performance threshold defaults** (early-exit thresholds, no thread settings):
   - `DEFAULT_POLYGON_COUNT_THRESHOLD`, `DEFAULT_LINE_SEGMENT_THRESHOLD`, `DEFAULT_ENTITY_COUNT_THRESHOLD`
   - Min/max ranges for each

2. **Precision setting defaults**:
   - `DEFAULT_ARC_FLATTENING_SAGITTA`, `DEFAULT_COORD_DEDUP_EPSILON`, `DEFAULT_ROTATION_TOLERANCE`
   - Min/max ranges for each

3. **Output setting defaults**:
   - `DEFAULT_AUTO_OPEN_EXCEL`, `DEFAULT_SHOW_SUCCESS_DIALOG`, `DEFAULT_INCLUDE_TIMESTAMP`, `DEFAULT_FILENAME_PREFIX`

4. **Logging setting defaults**:
   - `DEFAULT_LOG_VIEWER_LEVEL`, `DEFAULT_LOG_VIEWER_AUTO_SCROLL`, `DEFAULT_LOG_VIEWER_MAX_LINES`

5. **SETTINGS_VALIDATION_REGISTRY** dictionary:
   - Maps each setting name to its `SettingValidation` metadata
   - References both existing and new constants

### Phase 3: Integration

The TypedDicts and constants integrate with the existing codebase:
- `AppSettings` will be used by SettingsManager (B3) for type-safe settings storage
- `SettingValidation` will be used for runtime validation
- `SETTINGS_VALIDATION_REGISTRY` will be used by the Advanced Settings Window (C2) to show valid ranges

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add AppSettings TypedDict to types.py (B1 - Part 1)

Open `app/core/types.py` and add the `AppSettings` TypedDict after `BlockDefinitionRecord` (after line 271):

```python
class AppSettings(TypedDict, total=False):
    """
    Application settings for the DXF Block Extractor.

    All fields are optional (total=False) to allow partial updates.
    Used by SettingsManager for type-safe settings storage and validation.

    Categories:
    - Filters: Polygon filtering and gap bridging options
    - Performance: Early-exit thresholds for content zone detection
    - Precision: Numeric precision for geometry operations
    - Output: File output and Excel behavior settings
    - Logging: Log viewer and file logging configuration
    """

    # Filters (existing GUI options)
    unit_override: int | None
    precision_fix_enabled: bool
    precision_fix_amount: float | None
    gap_bridge_enabled: bool
    gap_bridge_amount: float | None
    min_area_filter_enabled: bool
    min_area_filter_amount: float | None
    min_side_filter_enabled: bool
    min_side_filter_amount: float | None

    # Performance (early-exit thresholds only - no thread settings)
    polygon_count_threshold: int
    line_segment_threshold: int
    entity_count_threshold: int

    # Precision
    arc_flattening_sagitta: float
    coord_dedup_epsilon: float
    rotation_tolerance: float

    # Output
    output_directory: str | None
    auto_open_excel: bool
    show_success_dialog: bool
    filename_prefix: str
    include_timestamp: bool

    # Logging
    generate_log_file: bool
    file_log_level: str
    log_viewer_level: str
    log_viewer_auto_scroll: bool
    log_viewer_max_lines: int
```

### Step 2: Add SettingValidation TypedDict to types.py (B1 - Part 2)

Add the `SettingValidation` TypedDict after `AppSettings`:

```python
class SettingValidation(TypedDict):
    """
    Validation metadata for a single application setting.

    Used by SETTINGS_VALIDATION_REGISTRY to define constraints and defaults
    for each setting in AppSettings.

    Attributes:
        min_value: Minimum allowed value for numeric settings, None for non-numeric
        max_value: Maximum allowed value for numeric settings, None for non-numeric
        default: Default value for the setting (type matches the setting type)
        unit_aware: True if default value varies based on drawing unit code
    """

    min_value: float | int | None
    max_value: float | int | None
    default: float | int | bool | str | None
    unit_aware: bool
```

### Step 3: Validate types.py Changes

Run type checking to ensure the new TypedDicts are correctly defined:

```bash
uv run mypy app/core/types.py
```

Expected: Success with no errors.

### Step 4: Add Performance Threshold Constants to constants.py (B2 - Part 1)

Open `app/core/constants.py` and add performance threshold constants at the end of the file (after line 304):

```python
# =============================================================================
# GUI Settings Defaults and Validation Ranges
# =============================================================================
# These constants support the Advanced Settings modal and SettingsManager.
# See ai_output/064-combined-gui-settings-and-parallel-removal-plan.md for context.

# Performance threshold defaults (early-exit thresholds only, no thread settings)
# Note: POLYGON_COUNT_THRESHOLD, LINE_SEGMENT_THRESHOLD, ENTITY_COUNT_THRESHOLD
# already exist above (lines 162-178). These DEFAULT_ versions are for the
# settings system; the originals remain for backward compatibility.
DEFAULT_POLYGON_COUNT_THRESHOLD: int = 500
DEFAULT_LINE_SEGMENT_THRESHOLD: int = 5000
DEFAULT_ENTITY_COUNT_THRESHOLD: int = 1000

POLYGON_COUNT_THRESHOLD_MIN: int = 100
POLYGON_COUNT_THRESHOLD_MAX: int = 10000
LINE_SEGMENT_THRESHOLD_MIN: int = 1000
LINE_SEGMENT_THRESHOLD_MAX: int = 50000
ENTITY_COUNT_THRESHOLD_MIN: int = 100
ENTITY_COUNT_THRESHOLD_MAX: int = 10000
```

### Step 5: Add Precision Setting Constants to constants.py (B2 - Part 2)

Add precision setting defaults after the performance thresholds:

```python
# Precision setting defaults
# Note: ARC_FLATTENING_SAGITTA already exists above (line 181).
# These provide explicit defaults and validation ranges for the settings system.
DEFAULT_ARC_FLATTENING_SAGITTA: float = 0.1
DEFAULT_COORD_DEDUP_EPSILON: float = 0.01
DEFAULT_ROTATION_TOLERANCE: float = 1.0

ARC_FLATTENING_SAGITTA_MIN: float = 0.01
ARC_FLATTENING_SAGITTA_MAX: float = 1.0
COORD_DEDUP_EPSILON_MIN: float = 0.001
COORD_DEDUP_EPSILON_MAX: float = 1.0
ROTATION_TOLERANCE_MIN: float = 0.1
ROTATION_TOLERANCE_MAX: float = 5.0
```

### Step 6: Add Output Setting Constants to constants.py (B2 - Part 3)

Add output setting defaults:

```python
# Output setting defaults
DEFAULT_AUTO_OPEN_EXCEL: bool = True
DEFAULT_SHOW_SUCCESS_DIALOG: bool = True
DEFAULT_INCLUDE_TIMESTAMP: bool = True
DEFAULT_FILENAME_PREFIX: str = ""
```

### Step 7: Add Logging Setting Constants to constants.py (B2 - Part 4)

Add logging setting defaults:

```python
# Logging setting defaults
DEFAULT_GENERATE_LOG_FILE: bool = False
DEFAULT_FILE_LOG_LEVEL: str = "DEBUG"
DEFAULT_LOG_VIEWER_LEVEL: str = "INFO"
DEFAULT_LOG_VIEWER_AUTO_SCROLL: bool = True
DEFAULT_LOG_VIEWER_MAX_LINES: int = 1000

LOG_VIEWER_MAX_LINES_MIN: int = 100
LOG_VIEWER_MAX_LINES_MAX: int = 10000
```

### Step 8: Add SETTINGS_VALIDATION_REGISTRY to constants.py (B2 - Part 5)

Add the validation registry dictionary at the end of constants.py. Import the SettingValidation type first:

**At the top of constants.py (after line 11, in the imports section if any, or add a new TYPE_CHECKING block):**

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import SettingValidation
```

**At the end of the file, add the registry:**

```python
# Settings Validation Registry
# Maps setting names to their validation metadata.
# Used by SettingsManager.validate() and Advanced Settings Window.
SETTINGS_VALIDATION_REGISTRY: dict[str, "SettingValidation"] = {
    # Filters
    "unit_override": {
        "min_value": -1,
        "max_value": 6,
        "default": None,
        "unit_aware": False,
    },
    "precision_fix_enabled": {
        "min_value": None,
        "max_value": None,
        "default": True,
        "unit_aware": False,
    },
    "precision_fix_amount": {
        "min_value": PRECISION_FIX_MIN,
        "max_value": PRECISION_FIX_MAX,
        "default": None,
        "unit_aware": True,
    },
    "gap_bridge_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "gap_bridge_amount": {
        "min_value": GAP_BRIDGE_MIN,
        "max_value": GAP_BRIDGE_MAX,
        "default": None,
        "unit_aware": True,
    },
    "min_area_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_area_filter_amount": {
        "min_value": MIN_AREA_FILTER_MIN,
        "max_value": MIN_AREA_FILTER_MAX,
        "default": None,
        "unit_aware": True,
    },
    "min_side_filter_enabled": {
        "min_value": None,
        "max_value": None,
        "default": False,
        "unit_aware": False,
    },
    "min_side_filter_amount": {
        "min_value": MIN_SIDE_FILTER_MIN,
        "max_value": MIN_SIDE_FILTER_MAX,
        "default": None,
        "unit_aware": True,
    },
    # Performance
    "polygon_count_threshold": {
        "min_value": POLYGON_COUNT_THRESHOLD_MIN,
        "max_value": POLYGON_COUNT_THRESHOLD_MAX,
        "default": DEFAULT_POLYGON_COUNT_THRESHOLD,
        "unit_aware": False,
    },
    "line_segment_threshold": {
        "min_value": LINE_SEGMENT_THRESHOLD_MIN,
        "max_value": LINE_SEGMENT_THRESHOLD_MAX,
        "default": DEFAULT_LINE_SEGMENT_THRESHOLD,
        "unit_aware": False,
    },
    "entity_count_threshold": {
        "min_value": ENTITY_COUNT_THRESHOLD_MIN,
        "max_value": ENTITY_COUNT_THRESHOLD_MAX,
        "default": DEFAULT_ENTITY_COUNT_THRESHOLD,
        "unit_aware": False,
    },
    # Precision
    "arc_flattening_sagitta": {
        "min_value": ARC_FLATTENING_SAGITTA_MIN,
        "max_value": ARC_FLATTENING_SAGITTA_MAX,
        "default": DEFAULT_ARC_FLATTENING_SAGITTA,
        "unit_aware": False,
    },
    "coord_dedup_epsilon": {
        "min_value": COORD_DEDUP_EPSILON_MIN,
        "max_value": COORD_DEDUP_EPSILON_MAX,
        "default": DEFAULT_COORD_DEDUP_EPSILON,
        "unit_aware": False,
    },
    "rotation_tolerance": {
        "min_value": ROTATION_TOLERANCE_MIN,
        "max_value": ROTATION_TOLERANCE_MAX,
        "default": DEFAULT_ROTATION_TOLERANCE,
        "unit_aware": False,
    },
    # Output
    "output_directory": {
        "min_value": None,
        "max_value": None,
        "default": None,
        "unit_aware": False,
    },
    "auto_open_excel": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_AUTO_OPEN_EXCEL,
        "unit_aware": False,
    },
    "show_success_dialog": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_SHOW_SUCCESS_DIALOG,
        "unit_aware": False,
    },
    "filename_prefix": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_FILENAME_PREFIX,
        "unit_aware": False,
    },
    "include_timestamp": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_INCLUDE_TIMESTAMP,
        "unit_aware": False,
    },
    # Logging
    "generate_log_file": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_GENERATE_LOG_FILE,
        "unit_aware": False,
    },
    "file_log_level": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_FILE_LOG_LEVEL,
        "unit_aware": False,
    },
    "log_viewer_level": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_LOG_VIEWER_LEVEL,
        "unit_aware": False,
    },
    "log_viewer_auto_scroll": {
        "min_value": None,
        "max_value": None,
        "default": DEFAULT_LOG_VIEWER_AUTO_SCROLL,
        "unit_aware": False,
    },
    "log_viewer_max_lines": {
        "min_value": LOG_VIEWER_MAX_LINES_MIN,
        "max_value": LOG_VIEWER_MAX_LINES_MAX,
        "default": DEFAULT_LOG_VIEWER_MAX_LINES,
        "unit_aware": False,
    },
}
```

### Step 9: Validate constants.py Changes

Run type checking to ensure the new constants are correctly defined:

```bash
uv run mypy app/core/constants.py
```

Expected: Success with no errors.

### Step 10: Add Unit Tests for New Constants

Open `app/tests/core/test_constants.py` and add tests for the new constants:

```python
class TestSettingsValidationRegistry:
    """Test suite for SETTINGS_VALIDATION_REGISTRY."""

    def test_registry_has_all_settings(self) -> None:
        """Test that registry contains all 24 expected settings."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        expected_settings = [
            # Filters
            "unit_override",
            "precision_fix_enabled",
            "precision_fix_amount",
            "gap_bridge_enabled",
            "gap_bridge_amount",
            "min_area_filter_enabled",
            "min_area_filter_amount",
            "min_side_filter_enabled",
            "min_side_filter_amount",
            # Performance
            "polygon_count_threshold",
            "line_segment_threshold",
            "entity_count_threshold",
            # Precision
            "arc_flattening_sagitta",
            "coord_dedup_epsilon",
            "rotation_tolerance",
            # Output
            "output_directory",
            "auto_open_excel",
            "show_success_dialog",
            "filename_prefix",
            "include_timestamp",
            # Logging
            "generate_log_file",
            "file_log_level",
            "log_viewer_level",
            "log_viewer_auto_scroll",
            "log_viewer_max_lines",
        ]
        assert len(SETTINGS_VALIDATION_REGISTRY) == 25
        for setting in expected_settings:
            assert setting in SETTINGS_VALIDATION_REGISTRY, f"Missing setting: {setting}"

    def test_registry_entries_have_required_keys(self) -> None:
        """Test that each registry entry has all required validation keys."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        required_keys = {"min_value", "max_value", "default", "unit_aware"}
        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            assert set(validation.keys()) == required_keys, (
                f"Setting '{setting_name}' has incorrect keys: {validation.keys()}"
            )

    def test_numeric_settings_have_valid_ranges(self) -> None:
        """Test that numeric settings have min <= max when both are defined."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            min_val = validation["min_value"]
            max_val = validation["max_value"]
            if min_val is not None and max_val is not None:
                assert min_val <= max_val, (
                    f"Setting '{setting_name}' has invalid range: {min_val} > {max_val}"
                )

    def test_default_values_within_range(self) -> None:
        """Test that default values are within their min/max range."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            default = validation["default"]
            min_val = validation["min_value"]
            max_val = validation["max_value"]

            # Skip if default is None or not numeric
            if default is None or not isinstance(default, (int, float)):
                continue

            if min_val is not None:
                assert default >= min_val, (
                    f"Setting '{setting_name}' default {default} < min {min_val}"
                )
            if max_val is not None:
                assert default <= max_val, (
                    f"Setting '{setting_name}' default {default} > max {max_val}"
                )

    def test_unit_aware_settings_identified(self) -> None:
        """Test that unit-aware settings are correctly flagged."""
        from core.constants import SETTINGS_VALIDATION_REGISTRY

        # These settings should have unit_aware=True (defaults vary by unit)
        unit_aware_settings = [
            "precision_fix_amount",
            "gap_bridge_amount",
            "min_area_filter_amount",
            "min_side_filter_amount",
        ]

        for setting_name in unit_aware_settings:
            assert SETTINGS_VALIDATION_REGISTRY[setting_name]["unit_aware"] is True, (
                f"Setting '{setting_name}' should be unit_aware"
            )

        # All other settings should have unit_aware=False
        for setting_name, validation in SETTINGS_VALIDATION_REGISTRY.items():
            if setting_name not in unit_aware_settings:
                assert validation["unit_aware"] is False, (
                    f"Setting '{setting_name}' should not be unit_aware"
                )


class TestSettingsDefaultConstants:
    """Test suite for settings default value constants."""

    def test_performance_threshold_defaults(self) -> None:
        """Test performance threshold default values."""
        from core.constants import (
            DEFAULT_ENTITY_COUNT_THRESHOLD,
            DEFAULT_LINE_SEGMENT_THRESHOLD,
            DEFAULT_POLYGON_COUNT_THRESHOLD,
        )

        assert DEFAULT_POLYGON_COUNT_THRESHOLD == 500
        assert DEFAULT_LINE_SEGMENT_THRESHOLD == 5000
        assert DEFAULT_ENTITY_COUNT_THRESHOLD == 1000

    def test_precision_setting_defaults(self) -> None:
        """Test precision setting default values."""
        from core.constants import (
            DEFAULT_ARC_FLATTENING_SAGITTA,
            DEFAULT_COORD_DEDUP_EPSILON,
            DEFAULT_ROTATION_TOLERANCE,
        )

        assert DEFAULT_ARC_FLATTENING_SAGITTA == 0.1
        assert DEFAULT_COORD_DEDUP_EPSILON == 0.01
        assert DEFAULT_ROTATION_TOLERANCE == 1.0

    def test_output_setting_defaults(self) -> None:
        """Test output setting default values."""
        from core.constants import (
            DEFAULT_AUTO_OPEN_EXCEL,
            DEFAULT_FILENAME_PREFIX,
            DEFAULT_INCLUDE_TIMESTAMP,
            DEFAULT_SHOW_SUCCESS_DIALOG,
        )

        assert DEFAULT_AUTO_OPEN_EXCEL is True
        assert DEFAULT_SHOW_SUCCESS_DIALOG is True
        assert DEFAULT_INCLUDE_TIMESTAMP is True
        assert DEFAULT_FILENAME_PREFIX == ""

    def test_logging_setting_defaults(self) -> None:
        """Test logging setting default values."""
        from core.constants import (
            DEFAULT_FILE_LOG_LEVEL,
            DEFAULT_GENERATE_LOG_FILE,
            DEFAULT_LOG_VIEWER_AUTO_SCROLL,
            DEFAULT_LOG_VIEWER_LEVEL,
            DEFAULT_LOG_VIEWER_MAX_LINES,
        )

        assert DEFAULT_GENERATE_LOG_FILE is False
        assert DEFAULT_FILE_LOG_LEVEL == "DEBUG"
        assert DEFAULT_LOG_VIEWER_LEVEL == "INFO"
        assert DEFAULT_LOG_VIEWER_AUTO_SCROLL is True
        assert DEFAULT_LOG_VIEWER_MAX_LINES == 1000
```

### Step 11: Run Validation Commands

Execute all validation commands to ensure the changes are correct.

## Testing Strategy

### Unit Tests

- Test `SETTINGS_VALIDATION_REGISTRY` has all 24 expected settings
- Test each registry entry has required keys (min_value, max_value, default, unit_aware)
- Test numeric settings have valid ranges (min <= max)
- Test default values are within their defined ranges
- Test unit-aware settings are correctly flagged
- Test individual default constant values

### Integration Tests

- Not applicable for this unit (data structures only)
- Integration testing will occur in B3 (SettingsManager) and C1 (GUI integration)

### Edge Cases

- Settings with None defaults (optional values)
- Settings with None min/max (non-numeric types like bool, str)
- Unit-aware settings with dictionary-based defaults

### Playwright MCP Tests

- Not applicable for this unit (no GUI components)
- E2E tests will be added in C2 (Advanced Settings Window)

## Acceptance Criteria

- [ ] `AppSettings` TypedDict defined in types.py with all 24 fields
- [ ] `SettingValidation` TypedDict defined in types.py
- [ ] All performance threshold constants defined in constants.py
- [ ] All precision setting constants defined in constants.py
- [ ] All output setting constants defined in constants.py
- [ ] All logging setting constants defined in constants.py
- [ ] `SETTINGS_VALIDATION_REGISTRY` dictionary defined with 25 entries
- [ ] mypy passes with no errors on both types.py and constants.py
- [ ] All existing tests continue to pass (856 tests)
- [ ] New unit tests for constants pass
- [ ] ruff check passes with no errors
- [ ] ruff format passes with no changes needed

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/types.py` - Type check types.py to ensure TypedDicts are correct
- `uv run mypy app/core/constants.py` - Type check constants.py to ensure new constants are correct
- `uv run mypy app/` - Full type check to catch any cascading issues
- `uv run ruff check app/core/types.py` - Lint types.py for code quality issues
- `uv run ruff check app/core/constants.py` - Lint constants.py for code quality issues
- `uv run ruff check app/tests/core/test_constants.py` - Lint new test file
- `uv run ruff format app/core/types.py --check` - Verify types.py formatting
- `uv run ruff format app/core/constants.py --check` - Verify constants.py formatting
- `uv run ruff format app/tests/core/test_constants.py --check` - Verify test file formatting
- `uv run pytest app/tests/core/test_constants.py -v` - Run constants tests including new tests
- `uv run pytest app/tests/ -v` - Run full test suite (should be 856+ tests, all passing)

## Notes

1. **Registry count is 25, not 24** - The plan mentions 24 settings, but `generate_log_file` was added for completeness, bringing the total to 25 settings. Update acceptance criteria if needed.

2. **Existing constants reused** - The registry references existing constants like `PRECISION_FIX_MIN`, `GAP_BRIDGE_MIN`, etc. that were already defined. This avoids duplication.

3. **TYPE_CHECKING import pattern** - Using `TYPE_CHECKING` for the `SettingValidation` import in constants.py avoids circular imports since types.py doesn't need to import from constants.py.

4. **Unit-aware defaults** - Four settings (`precision_fix_amount`, `gap_bridge_amount`, `min_area_filter_amount`, `min_side_filter_amount`) have `unit_aware=True` because their defaults vary based on the drawing's unit system. The actual unit-aware default lookup will be implemented in SettingsManager (B3).

5. **Backward compatibility** - Original constants like `POLYGON_COUNT_THRESHOLD` (line 162) remain unchanged. New `DEFAULT_POLYGON_COUNT_THRESHOLD` constants are added for the settings system. This preserves existing behavior.

6. **Reference document** - Full context available in `ai_output/064-combined-gui-settings-and-parallel-removal-plan.md`

7. **Lines of code impact**:
   - types.py: +55 lines (AppSettings and SettingValidation TypedDicts)
   - constants.py: +180 lines (defaults, ranges, and registry)
   - test_constants.py: +100 lines (new test class)

8. **After this unit completes**:
   - `AppSettings` and `SettingValidation` TypedDicts available for import
   - All settings have centralized defaults and validation ranges
   - Ready for Phase B3 (SettingsManager class implementation)
