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
                return (
                    False,
                    f"Expected numeric value for {key}, got {type(value).__name__}",
                )

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
                return PRECISION_SNAP_TOLERANCE.get(
                    unit_code, PRECISION_SNAP_TOLERANCE[0]
                )
            elif key == "gap_bridge_amount":
                return DEFAULT_GAP_CLOSURE_TOLERANCE.get(
                    unit_code, DEFAULT_GAP_CLOSURE_TOLERANCE[0]
                )
            elif key == "min_area_filter_amount":
                return DEFAULT_MIN_AREA_FILTER.get(
                    unit_code, DEFAULT_MIN_AREA_FILTER[0]
                )
            elif key == "min_side_filter_amount":
                return DEFAULT_MIN_SIDE_FILTER.get(
                    unit_code, DEFAULT_MIN_SIDE_FILTER[0]
                )

        return validation["default"]

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

    def reset_all(self) -> None:
        """Reset all settings to defaults."""
        with self._lock:
            self._settings.clear()

    def to_dict(self) -> "AppSettings":
        """Export current settings as AppSettings dict.

        Returns:
            Dictionary with all explicitly set settings.
            Settings at default values are not included.
        """
        with self._lock:
            # Return a copy to prevent external mutation
            return dict(self._settings)  # type: ignore[return-value]

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
            logger.warning(
                "Settings file does not contain a dictionary. Using defaults."
            )
            return False

        # Extract settings (ignore version for now, will be used for migration)
        settings_data = data.get("settings", data)  # Support both formats

        # Import with validation
        self.from_dict(settings_data)

        logger.debug(f"Loaded settings from {self._config_path}")
        return True

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

    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path
