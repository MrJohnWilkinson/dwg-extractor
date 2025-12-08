"""
Tests for constants module - Content Zone Detection Thresholds.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
"""

from core.constants import (
    CYCLE_DETECTION_TIMEOUT_SECONDS,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
    LINE_SEGMENT_THRESHOLD,
    POLYGON_COUNT_THRESHOLD,
)


class TestContentZoneThresholds:
    """Tests for content zone detection threshold constants."""

    def test_polygon_threshold_reasonable(self) -> None:
        """Threshold should be between 10 and 100."""
        assert 10 <= POLYGON_COUNT_THRESHOLD <= 100

    def test_line_threshold_reasonable(self) -> None:
        """Threshold should be between 50 and 500."""
        assert 50 <= LINE_SEGMENT_THRESHOLD <= 500

    def test_timeout_reasonable(self) -> None:
        """Timeout should be between 1 and 30 seconds."""
        assert 1.0 <= CYCLE_DETECTION_TIMEOUT_SECONDS <= 30.0


class TestContentZoneExcelColumns:
    """Tests for content zone Excel column constants."""

    def test_content_zone_excel_columns_follow_naming_convention(self) -> None:
        """All content zone columns should start with 'block_' prefix."""
        content_zone_columns = [
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
            EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
            EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
        ]

        for column in content_zone_columns:
            assert column.startswith("block_"), (
                f"Column '{column}' does not follow naming convention"
            )
