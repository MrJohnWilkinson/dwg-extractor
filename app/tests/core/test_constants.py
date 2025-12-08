"""
Tests for constants module - Content Zone Detection Thresholds.

Tests cover:
- Threshold constants are within reasonable bounds
- Excel column constants follow naming conventions
"""

from core.constants import (
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
        """Threshold should be between 10 and 1000.

        With Shapely's efficient GEOS-based operations, the threshold can be
        much higher than the original O(n^3) implementation. 500 is conservative.
        """
        assert 10 <= POLYGON_COUNT_THRESHOLD <= 1000

    def test_line_threshold_reasonable(self) -> None:
        """Threshold should be between 1000 and 10000.

        With Shapely's efficient GEOS-based polygonize(), the threshold can be
        much higher than the original DFS implementation. 5000 is conservative.
        """
        assert 1000 <= LINE_SEGMENT_THRESHOLD <= 10000


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
