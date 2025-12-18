"""
Unit tests for the excel_formatting module - All Blocks sheet.

This test suite validates All Blocks sheet formatting including:
- Auto-filter application
- Column width settings
- Frozen panes
- Three-tier scale highlighting (red, orange, yellow)
- Text wrapping for name and segment columns
"""

from typing import cast

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.constants import (
    EXCEL_FILL_COLOR_SCALE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
    EXCEL_SHEET_ALL_BLOCKS,
)
from core.excel_formatting import _format_all_blocks_sheet


class TestAllBlocksFormatting:
    """Test suite for _format_all_blocks_sheet function."""

    def _create_test_workbook_with_headers(self) -> tuple[Workbook, Worksheet]:
        """Create a test workbook with All Blocks sheet and headers."""
        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_ALL_BLOCKS

        # Add all 29 column headers
        headers = [
            "block_raw_name",
            "block_resolved_name",
            "block_suggested_trim_left",
            "block_suggested_trim_right",
            "block_suggested_trim_top",
            "block_suggested_trim_bottom",
            "block_vertical_segments",
            "block_horizontal_segments",
            "block_native_width",
            "block_native_height",
            "block_content_zone_detected",
            "block_content_zone_width",
            "block_content_zone_height",
            "block_polygon_count",
            "block_filtered_polygon_count",
            "block_insertion_status",
            "block_is_nested",
            "block_nested_parent_names",
            "block_entity_count",
            "block_insertion_count",
            "block_layer_count",
            "block_layer_names",
            "block_rotation_0",
            "block_rotation_90",
            "block_rotation_180",
            "block_rotation_270",
            "block_rotation_other",
            "block_scale_x",
            "block_scale_y",
        ]
        ws.append(headers)
        return wb, ws

    def test_format_all_blocks_autofilter(self) -> None:
        """Test that auto-filter is applied to All Blocks sheet."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a data row (new column order: identity, trim, segments, dimensions,
        # content zone, polygon counts, metadata, counts, layers, rotations, scales)
        ws.append(
            [
                "VALVE",  # A: raw_name
                "VALVE",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                1.0,  # AB: scale_x
                1.0,  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref == "A1:AC2"

    def test_format_all_blocks_column_widths(self) -> None:
        """Test that column widths are set correctly for all 29 columns."""
        wb, ws = self._create_test_workbook_with_headers()

        _format_all_blocks_sheet(wb)

        # Check key column widths (updated for new widths)
        assert ws.column_dimensions["A"].width == 35  # block_raw_name (was 30)
        assert ws.column_dimensions["B"].width == 35  # block_resolved_name (was 30)
        assert ws.column_dimensions["AB"].width == 12  # block_scale_x (was 15)
        assert ws.column_dimensions["AC"].width == 12  # block_scale_y (was 15)
        assert ws.column_dimensions["G"].width == 50  # block_vertical_segments (was 40)
        assert (
            ws.column_dimensions["H"].width == 50
        )  # block_horizontal_segments (was 40)
        assert (
            ws.column_dimensions["O"].width == 18
        )  # block_filtered_polygon_count (was 20)

    def test_format_all_blocks_frozen_panes(self) -> None:
        """Test that frozen panes are applied at B2 (header row and first column)."""
        wb, ws = self._create_test_workbook_with_headers()

        _format_all_blocks_sheet(wb)

        assert ws.freeze_panes == "B2"

    def test_format_all_blocks_red_highlighting_varies_negative(self) -> None:
        """Test that rows with VARIES (-) get red highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES (-) in x_scale (column AB = 28)
        ws.append(
            [
                "VALVE",  # A: raw_name
                "VALVE",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                "VARIES (-)",  # AB: scale_x
                1.0,  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have red fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
        assert cell_fill.fill_type == "solid"

    def test_format_all_blocks_orange_highlighting_negative_number(self) -> None:
        """Test that rows with single negative scale get orange highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with negative y_scale (column AC = 29)
        ws.append(
            [
                "PIPE",  # A: raw_name
                "PIPE",  # B: resolved_name
                20.0,  # C: trim_left
                20.0,  # D: trim_right
                10.0,  # E: trim_top
                10.0,  # F: trim_bottom
                "20, 160, 20",  # G: vertical_segments
                "10, 80, 10",  # H: horizontal_segments
                200.0,  # I: native_width
                100.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                160.0,  # L: content_zone_width
                80.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                12,  # S: entity_count
                5,  # T: insertion_count
                1,  # U: layer_count
                "Layer1",  # V: layer_names
                3,  # W: rotation_0
                0,  # X: rotation_90
                2,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                1.0,  # AB: scale_x
                -1.0,  # AC: scale_y (negative)
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have orange fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE
        assert cell_fill.fill_type == "solid"

    def test_format_all_blocks_yellow_highlighting_varies(self) -> None:
        """Test that rows with VARIES (positive only) get yellow highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES in x_scale (column AB = 28)
        ws.append(
            [
                "BLOCK1",  # A: raw_name
                "BLOCK1",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                "VARIES",  # AB: scale_x (positive variance)
                1.0,  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have yellow fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE
        assert cell_fill.fill_type == "solid"

    def test_format_all_blocks_no_highlighting_positive_scales(self) -> None:
        """Test that rows with positive uniform scales have no highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with positive uniform scales
        ws.append(
            [
                "BLOCK2",  # A: raw_name
                "BLOCK2",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                1,  # U: layer_count
                "Layer1",  # V: layer_names
                10,  # W: rotation_0
                0,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                1.0,  # AB: scale_x (positive)
                1.5,  # AC: scale_y (positive)
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should NOT have any of the scale highlighting colors
        cell_fill = ws.cell(row=2, column=1).fill
        if cell_fill.fill_type == "solid":
            assert cell_fill.start_color.rgb not in [
                EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
                EXCEL_FILL_COLOR_SCALE_NEGATIVE,
                EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
            ]

    def test_format_all_blocks_entire_row_highlighted(self) -> None:
        """Test that entire row (all 29 columns) is highlighted for scale issues."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES (-) to trigger red highlighting
        ws.append(
            [
                "VALVE",  # A: raw_name
                "VALVE",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                "VARIES (-)",  # AB: scale_x
                1.0,  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        # All 29 columns of row 2 should have red fill
        for col_idx in range(1, 30):
            cell_fill = ws.cell(row=2, column=col_idx).fill
            assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
            assert cell_fill.fill_type == "solid"

    def test_format_all_blocks_segment_columns_text_wrap(self) -> None:
        """Test that segment columns (G and H) have text wrapping with top alignment."""
        wb, ws = self._create_test_workbook_with_headers()

        ws.append(
            [
                "VALVE",  # A: raw_name
                "VALVE",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                1.0,  # AB: scale_x
                1.0,  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        # Column G (7 = vertical_segments) should have wrap_text with top vertical alignment
        g_cell = ws.cell(row=2, column=7)
        assert g_cell.alignment.wrap_text is True
        assert g_cell.alignment.vertical == "top"

        # Column H (8 = horizontal_segments) should have wrap_text with top vertical alignment
        h_cell = ws.cell(row=2, column=8)
        assert h_cell.alignment.wrap_text is True
        assert h_cell.alignment.vertical == "top"

    def test_format_all_blocks_header_text_wrap(self) -> None:
        """Test that header row has text wrap enabled."""
        wb, ws = self._create_test_workbook_with_headers()

        _format_all_blocks_sheet(wb)

        # All header cells should have wrap_text enabled
        for cell in ws[1]:
            assert cell.alignment.wrap_text is True

    def test_format_all_blocks_missing_sheet_handled(self) -> None:
        """Test that missing All Blocks sheet is handled gracefully."""
        wb = Workbook()
        # Sheet with different name
        ws = cast(Worksheet, wb.active)
        ws.title = "Other Sheet"

        # Should not raise an exception
        _format_all_blocks_sheet(wb)

    def test_format_all_blocks_highlighting_priority(self) -> None:
        """Test that VARIES (-) has higher priority than VARIES for highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES (-) in x and VARIES in y
        ws.append(
            [
                "MIXED",  # A: raw_name
                "MIXED",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                "VARIES (-)",  # AB: scale_x - should trigger red
                "VARIES",  # AC: scale_y - would trigger yellow but red wins
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have red fill (VARIES (-) takes priority)
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE

    def test_format_all_blocks_y_scale_varies_negative(self) -> None:
        """Test that VARIES (-) in y_scale also triggers red highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES (-) in y_scale
        ws.append(
            [
                "BLOCK_Y",  # A: raw_name
                "BLOCK_Y",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                1.0,  # AB: scale_x
                "VARIES (-)",  # AC: scale_y
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have red fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE

    def test_format_all_blocks_negative_x_scale(self) -> None:
        """Test that negative x_scale triggers orange highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with negative x_scale
        ws.append(
            [
                "BLOCK_NEG_X",  # A: raw_name
                "BLOCK_NEG_X",  # B: resolved_name
                10.0,  # C: trim_left
                10.0,  # D: trim_right
                5.0,  # E: trim_top
                5.0,  # F: trim_bottom
                "10, 80, 10",  # G: vertical_segments
                "5, 40, 5",  # H: horizontal_segments
                100.0,  # I: native_width
                50.0,  # J: native_height
                "TRUE",  # K: content_zone_detected
                80.0,  # L: content_zone_width
                40.0,  # M: content_zone_height
                2,  # N: polygon_count
                2,  # O: filtered_polygon_count
                "Inserted",  # P: insertion_status
                False,  # Q: is_nested
                "",  # R: parent_names
                8,  # S: entity_count
                10,  # T: insertion_count
                2,  # U: layer_count
                "Layer1, Layer2",  # V: layer_names
                5,  # W: rotation_0
                2,  # X: rotation_90
                0,  # Y: rotation_180
                0,  # Z: rotation_270
                0,  # AA: rotation_other
                -1.0,  # AB: scale_x (negative)
                1.0,  # AC: scale_y (positive)
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have orange fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE
