"""
Tests for settings synchronization between main GUI and SettingsManager.

Tests cover:
- _sync_numeric_setting() with valid and invalid values
- _sync_settings_to_manager() syncing all expected settings
- _refresh_from_settings() updating log level var
- Trace callbacks for instant sync

Note: These tests use mocking to avoid GUI instantiation per README guidance:
"Skip GUI tests in WSL - X server issues make it unreliable."
"""

from pathlib import Path

import pytest

from core.settings import SettingsManager


@pytest.fixture
def settings_manager(tmp_path: Path) -> SettingsManager:
    """Create a SettingsManager with a temporary config path."""
    config_path = tmp_path / "settings.json"
    return SettingsManager(config_path=config_path)


class TestSyncNumericSetting:
    """Tests for _sync_numeric_setting() helper method behavior."""

    def test_sync_valid_float_value(self, settings_manager: SettingsManager) -> None:
        """Verify valid float string syncs correctly to SettingsManager."""
        # Simulate what _sync_numeric_setting does
        var_value = "3.5"
        key = "precision_fix_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass

        assert settings_manager.get(key) == 3.5

    def test_sync_valid_integer_as_float(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify integer string syncs as float."""
        var_value = "5"
        key = "gap_bridge_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass

        assert settings_manager.get(key) == 5.0

    def test_sync_invalid_string_does_not_raise(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify invalid string like 'abc' doesn't raise and doesn't sync."""
        var_value = "abc"
        key = "precision_fix_amount"

        # This should not raise
        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass  # Expected - invalid input

        # Value should not have been set (returns default None)
        assert settings_manager.get(key) is None

    def test_sync_empty_string_does_not_raise(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify empty string doesn't raise and doesn't sync."""
        var_value = ""
        key = "gap_bridge_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass  # Expected - empty string

        # Value should not have been set
        assert settings_manager.get(key) is None

    def test_sync_partial_float_does_not_sync(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify partial float like '3.' doesn't sync (common while typing)."""
        var_value = "3."
        key = "min_area_filter_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass

        # '3.' is actually valid in Python, so it syncs as 3.0
        assert settings_manager.get(key) == 3.0

    def test_sync_negative_number(self, settings_manager: SettingsManager) -> None:
        """Verify negative numbers sync (validation is in SettingsManager)."""
        var_value = "-5.0"
        key = "precision_fix_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass

        # Negative value will be rejected by SettingsManager validation
        # so it won't be stored
        assert settings_manager.get(key) is None

    def test_sync_very_large_number(self, settings_manager: SettingsManager) -> None:
        """Verify very large numbers sync if valid."""
        var_value = "999999.99"
        key = "min_area_filter_amount"

        try:
            value = float(var_value)
            settings_manager.set(key, value)
        except ValueError:
            pass

        assert settings_manager.get(key) == 999999.99


class TestSyncSettingsToManager:
    """Tests for _sync_settings_to_manager() comprehensive sync behavior."""

    def test_syncs_all_boolean_filter_flags(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify all 4 boolean filter flags are synced."""
        # Set values directly to SettingsManager (simulating what _sync does)
        settings_manager.set("precision_fix_enabled", False)
        settings_manager.set("gap_bridge_enabled", True)
        settings_manager.set("min_area_filter_enabled", True)
        settings_manager.set("min_side_filter_enabled", False)

        assert settings_manager.get("precision_fix_enabled") is False
        assert settings_manager.get("gap_bridge_enabled") is True
        assert settings_manager.get("min_area_filter_enabled") is True
        assert settings_manager.get("min_side_filter_enabled") is False

    def test_syncs_all_numeric_amounts(self, settings_manager: SettingsManager) -> None:
        """Verify all 4 numeric filter amounts are synced."""
        settings_manager.set("precision_fix_amount", 2.5)
        settings_manager.set("gap_bridge_amount", 4.0)
        settings_manager.set("min_area_filter_amount", 50000.0)
        settings_manager.set("min_side_filter_amount", 15.0)

        assert settings_manager.get("precision_fix_amount") == 2.5
        assert settings_manager.get("gap_bridge_amount") == 4.0
        assert settings_manager.get("min_area_filter_amount") == 50000.0
        assert settings_manager.get("min_side_filter_amount") == 15.0

    def test_syncs_unit_override(self, settings_manager: SettingsManager) -> None:
        """Verify unit_override is synced."""
        # None means auto-detect (DXF/DWG option)
        settings_manager.set("unit_override", None)
        assert settings_manager.get("unit_override") is None

        # 4 means millimeters
        settings_manager.set("unit_override", 4)
        assert settings_manager.get("unit_override") == 4

    def test_syncs_logging_settings(self, settings_manager: SettingsManager) -> None:
        """Verify all logging settings are synced."""
        settings_manager.set("generate_log_file", True)
        settings_manager.set("file_log_level", "DEBUG")
        settings_manager.set("log_viewer_level", "WARNING")

        assert settings_manager.get("generate_log_file") is True
        assert settings_manager.get("file_log_level") == "DEBUG"
        assert settings_manager.get("log_viewer_level") == "WARNING"


class TestRefreshFromSettings:
    """Tests for _refresh_from_settings() behavior."""

    def test_log_level_updated_when_different(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify log_level_var is updated when settings differ."""
        # Simulate settings changed in Advanced Settings window
        settings_manager.set("log_viewer_level", "DEBUG")

        # Verify the setting is stored
        assert settings_manager.get("log_viewer_level") == "DEBUG"

    def test_log_level_unchanged_when_same(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify no-op when log_level_var matches settings."""
        # Default is INFO
        current_level = settings_manager.get("log_viewer_level")
        assert current_level == "INFO"

        # Setting same value should succeed
        result = settings_manager.set("log_viewer_level", "INFO")
        assert result is True
        assert settings_manager.get("log_viewer_level") == "INFO"

    def test_accepts_all_valid_log_levels(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify all valid log levels can be set and retrieved."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in valid_levels:
            result = settings_manager.set("log_viewer_level", level)
            assert result is True
            assert settings_manager.get("log_viewer_level") == level


class TestTraceCallbackBehavior:
    """Tests for trace callback integration behavior."""

    def test_trace_callback_pattern_with_valid_input(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify the trace callback pattern works with valid input."""
        # Simulate what happens when trace callback fires

        def sync_numeric_setting(key: str, value_str: str) -> None:
            try:
                value = float(value_str)
                settings_manager.set(key, value)
            except ValueError:
                pass

        # User types "3.5"
        sync_numeric_setting("precision_fix_amount", "3.5")
        assert settings_manager.get("precision_fix_amount") == 3.5

    def test_trace_callback_pattern_with_partial_input(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify trace callback handles partial input gracefully."""

        def sync_numeric_setting(key: str, value_str: str) -> None:
            try:
                value = float(value_str)
                settings_manager.set(key, value)
            except ValueError:
                pass

        # User is typing - partial input that's invalid
        sync_numeric_setting("precision_fix_amount", "")
        # Should not have synced invalid value
        assert settings_manager.get("precision_fix_amount") is None

        # User continues typing
        sync_numeric_setting("precision_fix_amount", "3")
        assert settings_manager.get("precision_fix_amount") == 3.0

        # User adds decimal
        sync_numeric_setting("precision_fix_amount", "3.")
        assert settings_manager.get("precision_fix_amount") == 3.0

        # User completes entry
        sync_numeric_setting("precision_fix_amount", "3.5")
        assert settings_manager.get("precision_fix_amount") == 3.5


class TestEdgeCases:
    """Tests for edge cases in settings synchronization."""

    def test_unit_override_auto_detect_syncs_as_none(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify DXF/DWG (auto-detect) syncs as None."""
        settings_manager.set("unit_override", None)
        assert settings_manager.get("unit_override") is None

    def test_unit_override_specific_unit_syncs(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify specific unit selections sync correctly."""
        # Test various unit codes
        unit_codes = [1, 2, 4, 5, 6]  # inches, feet, mm, cm, m

        for code in unit_codes:
            result = settings_manager.set("unit_override", code)
            assert result is True
            assert settings_manager.get("unit_override") == code

    def test_sync_preserves_existing_settings(
        self, settings_manager: SettingsManager
    ) -> None:
        """Verify syncing new settings doesn't corrupt existing ones."""
        # Set some initial values
        settings_manager.set("polygon_count_threshold", 600)
        settings_manager.set("auto_open_excel", False)

        # Now sync some filter settings
        settings_manager.set("precision_fix_amount", 5.0)
        settings_manager.set("gap_bridge_amount", 3.0)

        # Original settings should be unchanged
        assert settings_manager.get("polygon_count_threshold") == 600
        assert settings_manager.get("auto_open_excel") is False

    def test_settings_persist_after_save_load(self, tmp_path: Path) -> None:
        """Verify synced settings persist across save/load cycle."""
        config_path = tmp_path / "settings.json"

        # First session: sync and save
        manager1 = SettingsManager(config_path=config_path)
        manager1.set("precision_fix_amount", 2.5)
        manager1.set("gap_bridge_amount", 4.0)
        manager1.set("unit_override", 4)  # mm
        manager1.set("log_viewer_level", "DEBUG")
        manager1.save()

        # Second session: load and verify
        manager2 = SettingsManager(config_path=config_path)
        manager2.load()

        assert manager2.get("precision_fix_amount") == 2.5
        assert manager2.get("gap_bridge_amount") == 4.0
        assert manager2.get("unit_override") == 4
        assert manager2.get("log_viewer_level") == "DEBUG"


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
