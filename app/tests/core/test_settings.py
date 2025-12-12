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
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from core.constants import (
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


class TestSettingsManagerValidation:
    """Tests for validation logic."""

    def test_validate_valid_numeric_value(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify validation passes for valid numeric value."""
        is_valid, error = settings_manager.validate("polygon_count_threshold", 500)
        assert is_valid is True
        assert error == ""

    def test_validate_value_below_min(self, settings_manager: SettingsManager) -> None:
        """Verify validation fails for value below minimum."""
        is_valid, error = settings_manager.validate("polygon_count_threshold", 50)
        assert is_valid is False
        assert f">= {POLYGON_COUNT_THRESHOLD_MIN}" in error

    def test_validate_value_above_max(self, settings_manager: SettingsManager) -> None:
        """Verify validation fails for value above maximum."""
        is_valid, error = settings_manager.validate("polygon_count_threshold", 20000)
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

    def test_validate_unknown_setting(self, settings_manager: SettingsManager) -> None:
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


class TestSettingsManagerReset:
    """Tests for reset operations."""

    def test_reset_section_filters(self, populated_settings: SettingsManager) -> None:
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

    def test_to_dict_returns_copy(self, populated_settings: SettingsManager) -> None:
        """Verify to_dict returns a copy, not internal state."""
        result = populated_settings.to_dict()
        result["polygon_count_threshold"] = 999

        # Internal state should be unchanged
        assert populated_settings.get("polygon_count_threshold") == 600

    def test_from_dict_imports_valid_values(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify from_dict imports valid settings."""
        settings_manager.from_dict(
            {
                "polygon_count_threshold": 700,
                "auto_open_excel": False,
            }
        )

        assert settings_manager.get("polygon_count_threshold") == 700
        assert settings_manager.get("auto_open_excel") is False

    def test_from_dict_skips_invalid_values(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify from_dict skips invalid values without raising."""
        settings_manager.from_dict(
            {
                "polygon_count_threshold": 10,  # Below min
                "auto_open_excel": False,  # Valid
            }
        )

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
        settings_manager.from_dict(
            {
                "unknown_key": "value",  # type: ignore[typeddict-unknown-key]
                "auto_open_excel": False,
            }
        )

        assert settings_manager.get("auto_open_excel") is False


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

    def test_save_includes_version(self, settings_manager: SettingsManager) -> None:
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

    def test_settings_persist_across_restarts(self, tmp_path: Path) -> None:
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
                        POLYGON_COUNT_THRESHOLD_MIN + (i % 100),
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

    def test_concurrent_reset_and_set(self, settings_manager: SettingsManager) -> None:
        """Verify concurrent reset and set operations don't deadlock."""
        errors: list[Exception] = []

        def setter() -> None:
            try:
                for i in range(50):
                    settings_manager.set(
                        "polygon_count_threshold", POLYGON_COUNT_THRESHOLD_MIN + i
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
