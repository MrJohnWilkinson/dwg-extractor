# Feature: SettingsManager Class with Persistence (Unit 4 - Phases B3-B4)

## Feature Description

This specification covers the core SettingsManager class implementation for the GUI Settings infrastructure. It implements phases B3-B4 of the combined implementation plan (064-combined-gui-settings-and-parallel-removal-plan.md):

- **B3**: Create `SettingsManager` class in `app/core/settings.py` with get/set, validation, defaults, reset, and dict import/export
- **B4**: Add platform-specific config paths and JSON persistence (load/save)

The SettingsManager provides a centralized, thread-safe settings management system with:
- Type-safe get/set operations using the `AppSettings` TypedDict from Unit 3
- Validation against `SETTINGS_VALIDATION_REGISTRY` constraints
- Unit-aware default value resolution for geometry settings
- Platform-specific configuration file paths (Windows, macOS, Linux)
- JSON persistence with graceful error handling for corrupted files

**Scope:** B3-B4 only (SettingsManager class and persistence)

**Out of Scope (handled in later units):**
- C1: Main GUI migration to use SettingsManager
- C2: Advanced Settings Window modal
- D1-D2: Pipeline integration

**Prerequisites:**
- Unit 1 (A1-A3) completed: Parallel processing removed from extractor.py
- Unit 2 (A4-A6) completed: BlockAnalysisResult TypedDict deleted, tests updated
- Unit 3 (B1-B2) completed: AppSettings TypedDict, SettingValidation TypedDict, SETTINGS_VALIDATION_REGISTRY in constants.py

**Implementation Learnings from Previous Units:**
- Unit 1: Removed parallel processing from extractor.py
- Unit 2: Deleted BlockAnalysisResult TypedDict
- Unit 3: Added AppSettings (24 fields), SettingValidation TypedDict, SETTINGS_VALIDATION_REGISTRY (25 entries)
- Tests: 865 passing

## User Story

As a developer integrating the GUI Settings system
I want a centralized SettingsManager class with thread-safe operations and persistence
So that I can safely manage application settings from multiple components with automatic validation and cross-session persistence

## Problem Statement

The application needs centralized settings management to support the upcoming Advanced Settings modal. Currently:

1. No centralized class exists for settings management
2. Settings validation must be performed manually at each usage site
3. No persistence mechanism exists for user-configured settings
4. No thread-safe access pattern for settings shared across GUI and extraction threads
5. No unit-aware default resolution for geometry filter settings

## Solution Statement

Create a `SettingsManager` class in `app/core/settings.py` that provides:

1. **Centralized access** - Single source of truth for all application settings
2. **Validation** - Automatic validation using `SETTINGS_VALIDATION_REGISTRY`
3. **Type safety** - Operations aligned with `AppSettings` TypedDict
4. **Unit-aware defaults** - Resolve defaults based on drawing unit code for geometry settings
5. **Thread safety** - Use `threading.Lock` for concurrent access protection
6. **Platform-specific paths** - Config file location follows OS conventions
7. **JSON persistence** - Load/save with graceful error handling

## Relevant Files

Use these files to implement the feature:

- `app/core/types.py` - Contains `AppSettings` and `SettingValidation` TypedDicts (from Unit 3)
  - `AppSettings` at lines 274-322: TypedDict with 24 settings fields
  - `SettingValidation` at lines 325-343: TypedDict for validation metadata

- `app/core/constants.py` - Contains `SETTINGS_VALIDATION_REGISTRY` and default value constants (from Unit 3)
  - `SETTINGS_VALIDATION_REGISTRY` at lines 367-523: Maps setting names to validation metadata
  - Default value dictionaries: `DEFAULT_GAP_CLOSURE_TOLERANCE`, `DEFAULT_MIN_AREA_FILTER`, `DEFAULT_MIN_SIDE_FILTER`, `PRECISION_SNAP_TOLERANCE`
  - Default constants: `DEFAULT_POLYGON_COUNT_THRESHOLD`, `DEFAULT_ARC_FLATTENING_SAGITTA`, etc.

- `app/core/__init__.py` - May need update to export SettingsManager

### New Files

- `app/core/settings.py` - New file containing `SettingsManager` class
- `app/tests/core/test_settings.py` - New file containing unit tests for `SettingsManager`

## Implementation Plan

### Phase 1: Foundation (B3 - SettingsManager Class)

Create the core `SettingsManager` class with:

1. `__init__(self, config_path: Path | None = None)` - Initialize with optional custom path
2. `get(self, key: str) -> Any` - Get value with fallback to default
3. `set(self, key: str, value: Any) -> bool` - Set with validation, returns success
4. `validate(self, key: str, value: Any) -> tuple[bool, str]` - Validate with error message
5. `get_default(self, key: str, unit_code: int | None = None)` - Get default, optionally unit-aware
6. `reset_section(self, section: str) -> None` - Reset settings in section to defaults
7. `reset_all(self) -> None` - Reset all settings to defaults
8. `to_dict(self) -> AppSettings` - Export current settings
9. `from_dict(self, settings: AppSettings) -> None` - Import with validation
10. Thread safety using `threading.Lock`

### Phase 2: Core Implementation (B4 - Platform-Specific Paths and Persistence)

Add persistence layer:

1. `_get_config_path(self) -> Path` - Platform-specific path resolution
   - Windows: `%APPDATA%/DXFExtractor/settings.json`
   - macOS: `~/Library/Application Support/DXFExtractor/settings.json`
   - Linux: `$XDG_CONFIG_HOME/dxf-extractor/settings.json` (defaults to `~/.config`)

2. `load(self) -> bool` - Load from JSON, return True if file existed
   - Handle missing file (use defaults)
   - Handle corrupted JSON (use defaults with warning)
   - Validate loaded values against registry

3. `save(self) -> bool` - Save to JSON, return True on success
   - Create parent directories if needed
   - Include version field for future migration

### Phase 3: Integration

The SettingsManager integrates with:
- `AppSettings` TypedDict for type-safe operations
- `SETTINGS_VALIDATION_REGISTRY` for validation rules
- Unit-aware default dictionaries for geometry settings
- Logging module for warning messages on corrupted files

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Create settings.py Module Structure

Create `app/core/settings.py` with module docstring and imports:

```python
"""
Settings management for the DXF Block Extractor.

This module provides the SettingsManager class for centralized, thread-safe
settings management with validation and JSON persistence.

Usage:
    from core.settings import SettingsManager

    settings = SettingsManager()
    settings.load()  # Load from platform-specific config file

    # Get/set with validation
    value = settings.get("polygon_count_threshold")
    settings.set("polygon_count_threshold", 600)

    # Unit-aware defaults
    default = settings.get_default("gap_bridge_amount", unit_code=4)  # MM units

    # Persistence
    settings.save()
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .constants import (
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    PRECISION_SNAP_TOLERANCE,
    SETTINGS_VALIDATION_REGISTRY,
)

if TYPE_CHECKING:
    from .types import AppSettings

logger = logging.getLogger(__name__)

# Settings file version for future migration support
SETTINGS_VERSION: int = 1

# Section groupings for reset_section()
SETTINGS_SECTIONS: dict[str, list[str]] = {
    "filters": [
        "unit_override",
        "precision_fix_enabled",
        "precision_fix_amount",
        "gap_bridge_enabled",
        "gap_bridge_amount",
        "min_area_filter_enabled",
        "min_area_filter_amount",
        "min_side_filter_enabled",
        "min_side_filter_amount",
    ],
    "performance": [
        "polygon_count_threshold",
        "line_segment_threshold",
        "entity_count_threshold",
    ],
    "precision": [
        "arc_flattening_sagitta",
        "coord_dedup_epsilon",
        "rotation_tolerance",
    ],
    "output": [
        "output_directory",
        "auto_open_excel",
        "show_success_dialog",
        "filename_prefix",
        "include_timestamp",
    ],
    "logging": [
        "generate_log_file",
        "file_log_level",
        "log_viewer_level",
        "log_viewer_auto_scroll",
        "log_viewer_max_lines",
    ],
}
```

### Step 2: Implement SettingsManager.__init__ Method

Add the `__init__` method with thread lock and config path:

```python
class SettingsManager:
    """Manages application settings with validation and persistence.

    Thread-safe settings manager that provides:
    - Get/set operations with automatic validation
    - Unit-aware default value resolution
    - Section and full reset capabilities
    - JSON persistence with graceful error handling
    - Platform-specific configuration file paths

    Attributes:
        config_path: Path to the JSON settings file.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize with optional custom config path.

        Args:
            config_path: Custom path for settings file. If None, uses
                        platform-specific default location.
        """
        self._lock = threading.Lock()
        self._settings: dict[str, Any] = {}
        self._config_path = config_path if config_path else self._get_config_path()
```

### Step 3: Implement _get_config_path Method (B4)

Add platform-specific path resolution:

```python
    def _get_config_path(self) -> Path:
        """Get platform-appropriate config file path.

        Returns:
            Path to settings.json in platform-specific config directory:
            - Windows: %APPDATA%/DXFExtractor/settings.json
            - macOS: ~/Library/Application Support/DXFExtractor/settings.json
            - Linux: $XDG_CONFIG_HOME/dxf-extractor/settings.json
        """
        if sys.platform == "win32":
            base = Path(os.environ.get("APPDATA", Path.home()))
            return base / "DXFExtractor" / "settings.json"
        elif sys.platform == "darwin":
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "DXFExtractor"
                / "settings.json"
            )
        else:  # Linux and others
            xdg_config = os.environ.get("XDG_CONFIG_HOME", "")
            if xdg_config:
                base = Path(xdg_config)
            else:
                base = Path.home() / ".config"
            return base / "dxf-extractor" / "settings.json"
```

### Step 4: Implement get Method

Add the get method with thread safety and default fallback:

```python
    def get(self, key: str) -> Any:
        """Get setting value with fallback to default.

        Args:
            key: Setting name from AppSettings.

        Returns:
            Current value if set, otherwise the default from registry.

        Raises:
            KeyError: If key is not a valid setting name.
        """
        if key not in SETTINGS_VALIDATION_REGISTRY:
            raise KeyError(f"Unknown setting: {key}")

        with self._lock:
            if key in self._settings:
                return self._settings[key]

        # Return default (not stored in _settings)
        return self.get_default(key)
```

### Step 5: Implement validate Method

Add validation against registry constraints:

```python
    def validate(self, key: str, value: Any) -> tuple[bool, str]:
        """Validate value against setting constraints.

        Args:
            key: Setting name from AppSettings.
            value: Value to validate.

        Returns:
            Tuple of (is_valid, error_message). Error message is empty if valid.
        """
        if key not in SETTINGS_VALIDATION_REGISTRY:
            return False, f"Unknown setting: {key}"

        validation = SETTINGS_VALIDATION_REGISTRY[key]
        min_val = validation["min_value"]
        max_val = validation["max_value"]

        # None is always valid for optional settings (those with None default)
        if value is None:
            return True, ""

        # Type checking for numeric values
        if min_val is not None or max_val is not None:
            if not isinstance(value, (int, float)):
                return False, f"Expected numeric value for {key}, got {type(value).__name__}"

            if min_val is not None and value < min_val:
                return False, f"{key} must be >= {min_val}, got {value}"

            if max_val is not None and value > max_val:
                return False, f"{key} must be <= {max_val}, got {value}"

        # Type checking for boolean settings
        if isinstance(validation["default"], bool) and not isinstance(value, bool):
            # Allow None for optional booleans, but reject other types
            if value is not None:
                return False, f"Expected boolean for {key}, got {type(value).__name__}"

        # Type checking for string settings
        if isinstance(validation["default"], str) and not isinstance(value, str):
            if value is not None:
                return False, f"Expected string for {key}, got {type(value).__name__}"

        return True, ""
```

### Step 6: Implement set Method

Add the set method with validation:

```python
    def set(self, key: str, value: Any) -> bool:
        """Set and validate setting value.

        Args:
            key: Setting name from AppSettings.
            value: Value to set.

        Returns:
            True if value was valid and set, False if validation failed.
        """
        is_valid, error_msg = self.validate(key, value)
        if not is_valid:
            logger.warning(f"Invalid setting value: {error_msg}")
            return False

        with self._lock:
            self._settings[key] = value
        return True
```

### Step 7: Implement get_default Method

Add unit-aware default resolution:

```python
    def get_default(self, key: str, unit_code: int | None = None) -> Any:
        """Get default value for setting, optionally unit-aware.

        Args:
            key: Setting name from AppSettings.
            unit_code: DXF unit code for unit-aware settings (0-6).
                      Only used for precision_fix_amount, gap_bridge_amount,
                      min_area_filter_amount, min_side_filter_amount.

        Returns:
            Default value for the setting. For unit-aware settings, returns
            the value appropriate for the specified unit code.

        Raises:
            KeyError: If key is not a valid setting name.
        """
        if key not in SETTINGS_VALIDATION_REGISTRY:
            raise KeyError(f"Unknown setting: {key}")

        validation = SETTINGS_VALIDATION_REGISTRY[key]

        # Handle unit-aware settings
        if validation["unit_aware"] and unit_code is not None:
            # Use appropriate default dictionary based on setting
            if key == "precision_fix_amount":
                return PRECISION_SNAP_TOLERANCE.get(unit_code, PRECISION_SNAP_TOLERANCE[0])
            elif key == "gap_bridge_amount":
                return DEFAULT_GAP_CLOSURE_TOLERANCE.get(
                    unit_code, DEFAULT_GAP_CLOSURE_TOLERANCE[0]
                )
            elif key == "min_area_filter_amount":
                return DEFAULT_MIN_AREA_FILTER.get(unit_code, DEFAULT_MIN_AREA_FILTER[0])
            elif key == "min_side_filter_amount":
                return DEFAULT_MIN_SIDE_FILTER.get(unit_code, DEFAULT_MIN_SIDE_FILTER[0])

        return validation["default"]
```

### Step 8: Implement reset_section Method

Add section reset functionality:

```python
    def reset_section(self, section: str) -> None:
        """Reset all settings in section to defaults.

        Args:
            section: Section name (filters, performance, precision, output, logging).

        Raises:
            KeyError: If section is not a valid section name.
        """
        if section not in SETTINGS_SECTIONS:
            raise KeyError(
                f"Unknown section: {section}. "
                f"Valid sections: {', '.join(SETTINGS_SECTIONS.keys())}"
            )

        with self._lock:
            for key in SETTINGS_SECTIONS[section]:
                # Remove from _settings to fall back to default
                self._settings.pop(key, None)
```

### Step 9: Implement reset_all Method

Add full reset functionality:

```python
    def reset_all(self) -> None:
        """Reset all settings to defaults."""
        with self._lock:
            self._settings.clear()
```

### Step 10: Implement to_dict Method

Add export functionality:

```python
    def to_dict(self) -> "AppSettings":
        """Export current settings as AppSettings dict.

        Returns:
            Dictionary with all explicitly set settings.
            Settings at default values are not included.
        """
        with self._lock:
            # Return a copy to prevent external mutation
            return dict(self._settings)  # type: ignore[return-value]
```

### Step 11: Implement from_dict Method

Add import functionality with validation:

```python
    def from_dict(self, settings: "AppSettings") -> None:
        """Import settings from AppSettings dict with validation.

        Invalid values are skipped with a warning logged.
        Valid values are set, invalid values retain their previous state.

        Args:
            settings: Dictionary of settings to import.
        """
        for key, value in settings.items():
            if key not in SETTINGS_VALIDATION_REGISTRY:
                logger.warning(f"Skipping unknown setting: {key}")
                continue

            is_valid, error_msg = self.validate(key, value)
            if is_valid:
                with self._lock:
                    self._settings[key] = value
            else:
                logger.warning(f"Skipping invalid setting: {error_msg}")
```

### Step 12: Implement load Method (B4)

Add JSON loading with error handling:

```python
    def load(self) -> bool:
        """Load settings from JSON file.

        Handles missing files and corrupted JSON gracefully by using defaults.

        Returns:
            True if file existed and was loaded (even if some values invalid),
            False if file did not exist or was completely corrupted.
        """
        if not self._config_path.exists():
            logger.debug(f"Settings file not found: {self._config_path}")
            return False

        try:
            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Corrupted settings file {self._config_path}: {e}. Using defaults."
            )
            return False
        except OSError as e:
            logger.warning(f"Error reading settings file: {e}. Using defaults.")
            return False

        if not isinstance(data, dict):
            logger.warning("Settings file does not contain a dictionary. Using defaults.")
            return False

        # Extract settings (ignore version for now, will be used for migration)
        settings_data = data.get("settings", data)  # Support both formats

        # Import with validation
        self.from_dict(settings_data)  # type: ignore[arg-type]

        logger.debug(f"Loaded settings from {self._config_path}")
        return True
```

### Step 13: Implement save Method (B4)

Add JSON saving with directory creation:

```python
    def save(self) -> bool:
        """Save settings to JSON file.

        Creates parent directories if needed.
        Includes version field for future migration support.

        Returns:
            True on success, False on failure.
        """
        try:
            # Create parent directories if needed
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            # Build data structure with version
            data = {
                "version": SETTINGS_VERSION,
                "settings": self.to_dict(),
            }

            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved settings to {self._config_path}")
            return True
        except OSError as e:
            logger.error(f"Error saving settings: {e}")
            return False
```

### Step 14: Add config_path Property

Add read-only property for config path:

```python
    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path
```

### Step 15: Create Test File Structure

Create `app/tests/core/test_settings.py` with test imports and fixtures:

```python
"""
Tests for SettingsManager class.

Tests cover:
- Get/set operations with validation
- Default value resolution (including unit-aware)
- Section and full reset
- Dict import/export
- Platform-specific config paths
- JSON load/save with error handling
- Thread safety
"""

import json
import sys
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from core.constants import (
    DEFAULT_ARC_FLATTENING_SAGITTA,
    DEFAULT_GAP_CLOSURE_TOLERANCE,
    DEFAULT_MIN_AREA_FILTER,
    DEFAULT_MIN_SIDE_FILTER,
    DEFAULT_POLYGON_COUNT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD_MAX,
    POLYGON_COUNT_THRESHOLD_MIN,
    PRECISION_SNAP_TOLERANCE,
    SETTINGS_VALIDATION_REGISTRY,
)
from core.settings import SETTINGS_SECTIONS, SETTINGS_VERSION, SettingsManager


@pytest.fixture
def settings_manager(tmp_path: Path) -> SettingsManager:
    """Create a SettingsManager with a temporary config path."""
    config_path = tmp_path / "settings.json"
    return SettingsManager(config_path=config_path)


@pytest.fixture
def populated_settings(tmp_path: Path) -> SettingsManager:
    """Create a SettingsManager with some values set."""
    config_path = tmp_path / "settings.json"
    manager = SettingsManager(config_path=config_path)
    manager.set("polygon_count_threshold", 600)
    manager.set("auto_open_excel", False)
    manager.set("filename_prefix", "test_")
    return manager
```

### Step 16: Add Tests for Get/Set Operations

Add tests for basic get/set functionality:

```python
class TestSettingsManagerGetSet:
    """Tests for get/set operations."""

    def test_get_returns_default_when_not_set(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify get returns default value for unset settings."""
        value = settings_manager.get("polygon_count_threshold")
        assert value == DEFAULT_POLYGON_COUNT_THRESHOLD

    def test_get_returns_set_value(self, settings_manager: SettingsManager) -> None:
        """Verify get returns value after set."""
        settings_manager.set("polygon_count_threshold", 600)
        assert settings_manager.get("polygon_count_threshold") == 600

    def test_get_unknown_key_raises_keyerror(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify get raises KeyError for unknown setting."""
        with pytest.raises(KeyError, match="Unknown setting"):
            settings_manager.get("nonexistent_setting")

    def test_set_valid_value_returns_true(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify set returns True for valid value."""
        result = settings_manager.set("polygon_count_threshold", 600)
        assert result is True

    def test_set_invalid_value_returns_false(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify set returns False for invalid value."""
        # Value below minimum
        result = settings_manager.set("polygon_count_threshold", 10)
        assert result is False

    def test_set_invalid_value_does_not_change_setting(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify invalid set does not change current value."""
        settings_manager.set("polygon_count_threshold", 600)
        settings_manager.set("polygon_count_threshold", 10)  # Invalid, below min
        assert settings_manager.get("polygon_count_threshold") == 600

    def test_set_none_for_optional_setting(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify None can be set for optional settings."""
        result = settings_manager.set("output_directory", None)
        assert result is True
        assert settings_manager.get("output_directory") is None

    def test_set_string_value(self, settings_manager: SettingsManager) -> None:
        """Verify string setting can be set."""
        result = settings_manager.set("filename_prefix", "export_")
        assert result is True
        assert settings_manager.get("filename_prefix") == "export_"

    def test_set_boolean_value(self, settings_manager: SettingsManager) -> None:
        """Verify boolean setting can be set."""
        result = settings_manager.set("auto_open_excel", False)
        assert result is True
        assert settings_manager.get("auto_open_excel") is False
```

### Step 17: Add Tests for Validation

Add tests for validate method:

```python
class TestSettingsManagerValidation:
    """Tests for validation logic."""

    def test_validate_valid_numeric_value(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation passes for valid numeric value."""
        is_valid, error = settings_manager.validate("polygon_count_threshold", 500)
        assert is_valid is True
        assert error == ""

    def test_validate_value_below_min(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for value below minimum."""
        is_valid, error = settings_manager.validate("polygon_count_threshold", 50)
        assert is_valid is False
        assert f">= {POLYGON_COUNT_THRESHOLD_MIN}" in error

    def test_validate_value_above_max(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for value above maximum."""
        is_valid, error = settings_manager.validate(
            "polygon_count_threshold", 20000
        )
        assert is_valid is False
        assert f"<= {POLYGON_COUNT_THRESHOLD_MAX}" in error

    def test_validate_wrong_type_for_numeric(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for wrong type on numeric setting."""
        is_valid, error = settings_manager.validate(
            "polygon_count_threshold", "not a number"
        )
        assert is_valid is False
        assert "numeric" in error.lower()

    def test_validate_wrong_type_for_boolean(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for wrong type on boolean setting."""
        is_valid, error = settings_manager.validate("auto_open_excel", "yes")
        assert is_valid is False
        assert "boolean" in error.lower()

    def test_validate_wrong_type_for_string(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for wrong type on string setting."""
        is_valid, error = settings_manager.validate("filename_prefix", 123)
        assert is_valid is False
        assert "string" in error.lower()

    def test_validate_unknown_setting(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation fails for unknown setting."""
        is_valid, error = settings_manager.validate("unknown_setting", 100)
        assert is_valid is False
        assert "Unknown setting" in error

    def test_validate_none_for_optional(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify None is valid for optional settings."""
        is_valid, error = settings_manager.validate("output_directory", None)
        assert is_valid is True
```

### Step 18: Add Tests for get_default with Unit Awareness

Add tests for unit-aware defaults:

```python
class TestSettingsManagerDefaults:
    """Tests for default value resolution."""

    def test_get_default_non_unit_aware(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify get_default returns registry default for non-unit-aware settings."""
        default = settings_manager.get_default("polygon_count_threshold")
        assert default == DEFAULT_POLYGON_COUNT_THRESHOLD

    def test_get_default_unit_aware_without_unit_code(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify get_default returns registry default when no unit code provided."""
        default = settings_manager.get_default("gap_bridge_amount")
        assert default is None  # Registry default is None for unit-aware

    def test_get_default_gap_bridge_with_mm_unit(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify gap_bridge_amount default for MM units."""
        default = settings_manager.get_default("gap_bridge_amount", unit_code=4)
        assert default == DEFAULT_GAP_CLOSURE_TOLERANCE[4]  # MM

    def test_get_default_gap_bridge_with_inch_unit(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify gap_bridge_amount default for inch units."""
        default = settings_manager.get_default("gap_bridge_amount", unit_code=1)
        assert default == DEFAULT_GAP_CLOSURE_TOLERANCE[1]  # Inches

    def test_get_default_precision_fix_with_unit(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify precision_fix_amount uses PRECISION_SNAP_TOLERANCE."""
        default = settings_manager.get_default("precision_fix_amount", unit_code=4)
        assert default == PRECISION_SNAP_TOLERANCE[4]

    def test_get_default_min_area_with_unit(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify min_area_filter_amount uses DEFAULT_MIN_AREA_FILTER."""
        default = settings_manager.get_default("min_area_filter_amount", unit_code=4)
        assert default == DEFAULT_MIN_AREA_FILTER[4]

    def test_get_default_min_side_with_unit(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify min_side_filter_amount uses DEFAULT_MIN_SIDE_FILTER."""
        default = settings_manager.get_default("min_side_filter_amount", unit_code=4)
        assert default == DEFAULT_MIN_SIDE_FILTER[4]

    def test_get_default_unknown_unit_code_uses_unitless(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify unknown unit code falls back to unitless (0)."""
        default = settings_manager.get_default("gap_bridge_amount", unit_code=99)
        assert default == DEFAULT_GAP_CLOSURE_TOLERANCE[0]

    def test_get_default_unknown_setting_raises_keyerror(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify get_default raises KeyError for unknown setting."""
        with pytest.raises(KeyError, match="Unknown setting"):
            settings_manager.get_default("nonexistent_setting")
```

### Step 19: Add Tests for Reset Operations

Add tests for reset_section and reset_all:

```python
class TestSettingsManagerReset:
    """Tests for reset operations."""

    def test_reset_section_filters(
        self, populated_settings: SettingsManager
    ) -> None:
        """Verify reset_section resets only filter settings."""
        populated_settings.set("precision_fix_enabled", False)
        populated_settings.set("polygon_count_threshold", 700)  # Performance section

        populated_settings.reset_section("filters")

        # Filter setting should be reset to default
        assert populated_settings.get("precision_fix_enabled") is True
        # Performance setting should be unchanged
        assert populated_settings.get("polygon_count_threshold") == 700

    def test_reset_section_performance(
        self, populated_settings: SettingsManager
    ) -> None:
        """Verify reset_section resets only performance settings."""
        populated_settings.reset_section("performance")

        # Should be back to default
        assert (
            populated_settings.get("polygon_count_threshold")
            == DEFAULT_POLYGON_COUNT_THRESHOLD
        )

    def test_reset_section_unknown_raises_keyerror(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify reset_section raises KeyError for unknown section."""
        with pytest.raises(KeyError, match="Unknown section"):
            settings_manager.reset_section("nonexistent")

    def test_reset_all_clears_all_settings(
        self, populated_settings: SettingsManager
    ) -> None:
        """Verify reset_all clears all explicitly set values."""
        populated_settings.reset_all()

        # All should be back to defaults
        assert (
            populated_settings.get("polygon_count_threshold")
            == DEFAULT_POLYGON_COUNT_THRESHOLD
        )
        assert populated_settings.get("auto_open_excel") is True
        assert populated_settings.get("filename_prefix") == ""

    def test_settings_sections_covers_all_settings(self) -> None:
        """Verify SETTINGS_SECTIONS includes all registry settings."""
        all_section_settings = set()
        for settings_list in SETTINGS_SECTIONS.values():
            all_section_settings.update(settings_list)

        registry_settings = set(SETTINGS_VALIDATION_REGISTRY.keys())
        assert all_section_settings == registry_settings
```

### Step 20: Add Tests for Dict Import/Export

Add tests for to_dict and from_dict:

```python
class TestSettingsManagerDictOperations:
    """Tests for dict import/export."""

    def test_to_dict_returns_set_values(
        self, populated_settings: SettingsManager
    ) -> None:
        """Verify to_dict returns only explicitly set values."""
        result = populated_settings.to_dict()

        assert result["polygon_count_threshold"] == 600
        assert result["auto_open_excel"] is False
        assert result["filename_prefix"] == "test_"
        # Default values should not be in the dict
        assert "arc_flattening_sagitta" not in result

    def test_to_dict_returns_copy(
        self, populated_settings: SettingsManager
    ) -> None:
        """Verify to_dict returns a copy, not internal state."""
        result = populated_settings.to_dict()
        result["polygon_count_threshold"] = 999

        # Internal state should be unchanged
        assert populated_settings.get("polygon_count_threshold") == 600

    def test_from_dict_imports_valid_values(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify from_dict imports valid settings."""
        settings_manager.from_dict({
            "polygon_count_threshold": 700,
            "auto_open_excel": False,
        })

        assert settings_manager.get("polygon_count_threshold") == 700
        assert settings_manager.get("auto_open_excel") is False

    def test_from_dict_skips_invalid_values(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify from_dict skips invalid values without raising."""
        settings_manager.from_dict({
            "polygon_count_threshold": 10,  # Below min
            "auto_open_excel": False,  # Valid
        })

        # Invalid value should be skipped, default used
        assert (
            settings_manager.get("polygon_count_threshold")
            == DEFAULT_POLYGON_COUNT_THRESHOLD
        )
        # Valid value should be imported
        assert settings_manager.get("auto_open_excel") is False

    def test_from_dict_skips_unknown_keys(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify from_dict skips unknown keys without raising."""
        settings_manager.from_dict({
            "unknown_key": "value",
            "auto_open_excel": False,
        })

        assert settings_manager.get("auto_open_excel") is False
```

### Step 21: Add Tests for Platform-Specific Paths

Add tests for config path resolution:

```python
class TestSettingsManagerConfigPath:
    """Tests for platform-specific config paths."""

    def test_custom_config_path_used(self, tmp_path: Path) -> None:
        """Verify custom config path is used when provided."""
        custom_path = tmp_path / "custom" / "settings.json"
        manager = SettingsManager(config_path=custom_path)

        assert manager.config_path == custom_path

    @patch("sys.platform", "win32")
    @patch.dict("os.environ", {"APPDATA": "/Users/test/AppData/Roaming"})
    def test_windows_config_path(self) -> None:
        """Verify Windows uses APPDATA path."""
        manager = SettingsManager()
        expected = Path("/Users/test/AppData/Roaming/DXFExtractor/settings.json")
        assert manager.config_path == expected

    @patch("sys.platform", "darwin")
    def test_macos_config_path(self) -> None:
        """Verify macOS uses Library/Application Support path."""
        manager = SettingsManager()
        expected = (
            Path.home()
            / "Library"
            / "Application Support"
            / "DXFExtractor"
            / "settings.json"
        )
        assert manager.config_path == expected

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {"XDG_CONFIG_HOME": "/home/test/.config"}, clear=False)
    def test_linux_config_path_with_xdg(self) -> None:
        """Verify Linux uses XDG_CONFIG_HOME when set."""
        manager = SettingsManager()
        expected = Path("/home/test/.config/dxf-extractor/settings.json")
        assert manager.config_path == expected

    @patch("sys.platform", "linux")
    @patch.dict("os.environ", {}, clear=True)
    def test_linux_config_path_without_xdg(self) -> None:
        """Verify Linux falls back to ~/.config when XDG not set."""
        manager = SettingsManager()
        expected = Path.home() / ".config" / "dxf-extractor" / "settings.json"
        assert manager.config_path == expected
```

### Step 22: Add Tests for Load/Save Persistence

Add tests for JSON persistence:

```python
class TestSettingsManagerPersistence:
    """Tests for JSON load/save operations."""

    def test_save_creates_file(self, settings_manager: SettingsManager) -> None:
        """Verify save creates the settings file."""
        settings_manager.set("polygon_count_threshold", 600)
        result = settings_manager.save()

        assert result is True
        assert settings_manager.config_path.exists()

    def test_save_creates_parent_directories(self, tmp_path: Path) -> None:
        """Verify save creates parent directories if needed."""
        config_path = tmp_path / "deep" / "nested" / "settings.json"
        manager = SettingsManager(config_path=config_path)
        manager.set("auto_open_excel", False)

        result = manager.save()

        assert result is True
        assert config_path.exists()

    def test_save_includes_version(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify saved file includes version field."""
        settings_manager.save()

        with open(settings_manager.config_path) as f:
            data = json.load(f)

        assert data["version"] == SETTINGS_VERSION

    def test_load_returns_false_for_missing_file(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load returns False when file doesn't exist."""
        result = settings_manager.load()
        assert result is False

    def test_load_returns_true_for_existing_file(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load returns True when file exists."""
        settings_manager.set("polygon_count_threshold", 600)
        settings_manager.save()

        # Create new manager and load
        new_manager = SettingsManager(config_path=settings_manager.config_path)
        result = new_manager.load()

        assert result is True

    def test_load_restores_saved_values(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load restores previously saved values."""
        settings_manager.set("polygon_count_threshold", 600)
        settings_manager.set("auto_open_excel", False)
        settings_manager.save()

        # Create new manager and load
        new_manager = SettingsManager(config_path=settings_manager.config_path)
        new_manager.load()

        assert new_manager.get("polygon_count_threshold") == 600
        assert new_manager.get("auto_open_excel") is False

    def test_load_handles_corrupted_json(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load handles corrupted JSON gracefully."""
        # Write invalid JSON
        settings_manager.config_path.parent.mkdir(parents=True, exist_ok=True)
        settings_manager.config_path.write_text("not valid json {{{")

        result = settings_manager.load()

        assert result is False
        # Should use defaults
        assert (
            settings_manager.get("polygon_count_threshold")
            == DEFAULT_POLYGON_COUNT_THRESHOLD
        )

    def test_load_handles_non_dict_json(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load handles non-dict JSON gracefully."""
        settings_manager.config_path.parent.mkdir(parents=True, exist_ok=True)
        settings_manager.config_path.write_text('["not", "a", "dict"]')

        result = settings_manager.load()

        assert result is False

    def test_load_skips_invalid_values_in_file(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load skips invalid values from file."""
        # Write file with invalid value
        settings_manager.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "settings": {
                "polygon_count_threshold": 10,  # Below min
                "auto_open_excel": False,  # Valid
            }
        }
        settings_manager.config_path.write_text(json.dumps(data))

        settings_manager.load()

        # Invalid value should be skipped
        assert (
            settings_manager.get("polygon_count_threshold")
            == DEFAULT_POLYGON_COUNT_THRESHOLD
        )
        # Valid value should be loaded
        assert settings_manager.get("auto_open_excel") is False

    def test_load_supports_legacy_format(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify load supports files without version wrapper."""
        # Write legacy format (direct settings dict)
        settings_manager.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"polygon_count_threshold": 600}
        settings_manager.config_path.write_text(json.dumps(data))

        result = settings_manager.load()

        assert result is True
        assert settings_manager.get("polygon_count_threshold") == 600

    def test_settings_persist_across_restarts(
        self, tmp_path: Path
    ) -> None:
        """Verify settings persist across application restarts."""
        config_path = tmp_path / "settings.json"

        # First "session"
        manager1 = SettingsManager(config_path=config_path)
        manager1.set("polygon_count_threshold", 800)
        manager1.set("filename_prefix", "session1_")
        manager1.save()

        # Second "session"
        manager2 = SettingsManager(config_path=config_path)
        manager2.load()

        assert manager2.get("polygon_count_threshold") == 800
        assert manager2.get("filename_prefix") == "session1_"
```

### Step 23: Add Tests for Thread Safety

Add tests for thread-safe operations:

```python
class TestSettingsManagerThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_get_set(self, settings_manager: SettingsManager) -> None:
        """Verify concurrent get/set operations don't corrupt state."""
        errors: list[Exception] = []
        results: list[int] = []

        def writer() -> None:
            try:
                for i in range(100):
                    settings_manager.set(
                        "polygon_count_threshold",
                        POLYGON_COUNT_THRESHOLD_MIN + (i % 100)
                    )
            except Exception as e:
                errors.append(e)

        def reader() -> None:
            try:
                for _ in range(100):
                    value = settings_manager.get("polygon_count_threshold")
                    results.append(value)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # All read values should be valid
        for value in results:
            assert POLYGON_COUNT_THRESHOLD_MIN <= value <= POLYGON_COUNT_THRESHOLD_MAX

    def test_concurrent_reset_and_set(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify concurrent reset and set operations don't deadlock."""
        errors: list[Exception] = []

        def setter() -> None:
            try:
                for i in range(50):
                    settings_manager.set(
                        "polygon_count_threshold",
                        POLYGON_COUNT_THRESHOLD_MIN + i
                    )
            except Exception as e:
                errors.append(e)

        def resetter() -> None:
            try:
                for _ in range(50):
                    settings_manager.reset_all()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=setter),
            threading.Thread(target=resetter),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
```

### Step 24: Run Validation Commands

Execute validation commands to ensure implementation is correct:

```bash
# Type checking
uv run mypy app/core/settings.py

# Run new tests
uv run pytest app/tests/core/test_settings.py -v

# Full type check
uv run mypy app/

# Lint new files
uv run ruff check app/core/settings.py
uv run ruff check app/tests/core/test_settings.py

# Format check
uv run ruff format app/core/settings.py --check
uv run ruff format app/tests/core/test_settings.py --check

# Full test suite to ensure no regressions
uv run pytest app/tests/ -v
```

## Testing Strategy

### Unit Tests

- Test all public methods of SettingsManager
- Test get/set with valid and invalid values
- Test validation for all setting types (numeric, boolean, string)
- Test unit-aware default resolution for all 4 unit-aware settings
- Test all 5 sections in reset_section
- Test dict import/export round-trip
- Test platform-specific path detection
- Test JSON load with missing, corrupted, and valid files
- Test JSON save with directory creation

### Integration Tests

- Test settings persist across SettingsManager instances (simulated restart)
- Test thread safety with concurrent get/set/reset operations

### Edge Cases

- Unknown setting keys in get/set/validate/get_default
- None values for optional settings
- Unknown unit codes for unit-aware defaults
- Corrupted JSON file (syntax error)
- JSON file with wrong structure (array instead of dict)
- Missing parent directories for config file
- Concurrent access from multiple threads

### Playwright MCP Tests

- Not applicable for this unit (no GUI components)
- E2E tests will be added in C2 (Advanced Settings Window)

## Acceptance Criteria

- [ ] SettingsManager class created in `app/core/settings.py`
- [ ] `__init__` accepts optional custom config path
- [ ] `get()` returns default when setting not explicitly set
- [ ] `set()` validates and rejects out-of-range values, returns bool
- [ ] `validate()` provides helpful error messages
- [ ] `get_default()` handles unit-aware settings correctly (4 settings)
- [ ] `reset_section()` resets only settings in specified section
- [ ] `reset_all()` resets all settings to defaults
- [ ] `to_dict()` exports current settings as AppSettings
- [ ] `from_dict()` imports settings with validation
- [ ] Config path follows platform conventions (APPDATA, XDG_CONFIG_HOME, Library/Application Support)
- [ ] `load()` handles missing file gracefully (returns False, uses defaults)
- [ ] `load()` handles corrupted JSON gracefully (returns False with warning, uses defaults)
- [ ] `save()` creates parent directories if needed
- [ ] `save()` includes version field for future migration
- [ ] Settings persist across application restarts
- [ ] Thread-safe access using threading.Lock
- [ ] Unit tests cover all public methods
- [ ] mypy passes with no errors
- [ ] ruff check passes with no errors
- [ ] ruff format passes with no changes needed
- [ ] All existing tests continue to pass (865+ tests)

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/core/settings.py` - Type check new settings module
- `uv run mypy app/` - Full type check to catch any cascading issues
- `uv run ruff check app/core/settings.py` - Lint settings.py for code quality issues
- `uv run ruff check app/tests/core/test_settings.py` - Lint test file
- `uv run ruff format app/core/settings.py --check` - Verify settings.py formatting
- `uv run ruff format app/tests/core/test_settings.py --check` - Verify test file formatting
- `uv run pytest app/tests/core/test_settings.py -v` - Run new settings tests
- `uv run pytest app/tests/ -v` - Run full test suite (should be 865+ tests, all passing)

## Notes

1. **Thread safety implementation** - Uses a single `threading.Lock` for all operations. This is simple and safe but means only one operation can happen at a time. For this application's use case (GUI + single extraction thread), this is sufficient.

2. **Unit-aware defaults** - Four settings use unit-aware defaults:
   - `precision_fix_amount` -> `PRECISION_SNAP_TOLERANCE`
   - `gap_bridge_amount` -> `DEFAULT_GAP_CLOSURE_TOLERANCE`
   - `min_area_filter_amount` -> `DEFAULT_MIN_AREA_FILTER`
   - `min_side_filter_amount` -> `DEFAULT_MIN_SIDE_FILTER`

3. **Version field** - The saved JSON includes a `version` field for future migration support. Currently version 1. The load method supports both versioned format (`{"version": 1, "settings": {...}}`) and legacy format (direct settings dict).

4. **Error handling philosophy** - Invalid settings in `from_dict()` and `load()` are skipped with warnings rather than raising exceptions. This ensures the application can always start, even with a partially corrupted config file.

5. **Section definitions** - `SETTINGS_SECTIONS` maps section names to setting keys. This is used by `reset_section()` and will later be used by the Advanced Settings Window tabs.

6. **Lines of code impact**:
   - settings.py: ~250 lines (SettingsManager class)
   - test_settings.py: ~400 lines (comprehensive test coverage)

7. **After this unit completes**:
   - SettingsManager class available for import
   - Full persistence and validation support
   - Ready for Phase C1 (Main GUI Migration to use SettingsManager)
