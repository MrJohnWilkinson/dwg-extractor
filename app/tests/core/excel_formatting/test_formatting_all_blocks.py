"""
Unit tests for the excel_formatting module - All Blocks sheet.

This test suite validates All Blocks sheet formatting including:
- Auto-filter application
- Column width settings
- Frozen panes
- Three-tier scale highlighting (red, orange, yellow)
- Segment column right-alignment
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
            "block_native_width",
            "block_native_height",
            "block_vertical_segments",
            "block_horizontal_segments",
            "block_suggested_trim_left",
            "block_suggested_trim_right",
            "block_suggested_trim_top",
            "block_suggested_trim_bottom",
            "block_content_zone_detected",
            "block_content_zone_width",
            "block_content_zone_height",
            "block_polygon_count",
            "block_filtered_polygon_count",
        ]
        ws.append(headers)
        return wb, ws

    def test_format_all_blocks_autofilter(self) -> None:
        """Test that auto-filter is applied to All Blocks sheet."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a data row
        ws.append(
            [
                "VALVE",
                "VALVE",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                1.0,
                1.0,
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
            ]
        )

        _format_all_blocks_sheet(wb)

        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref == "A1:AC2"

    def test_format_all_blocks_column_widths(self) -> None:
        """Test that column widths are set correctly for all 29 columns."""
        wb, ws = self._create_test_workbook_with_headers()

        _format_all_blocks_sheet(wb)

        # Check key column widths
        assert ws.column_dimensions["A"].width == 30  # block_raw_name
        assert ws.column_dimensions["B"].width == 30  # block_resolved_name
        assert ws.column_dimensions["O"].width == 15  # block_scale_x
        assert ws.column_dimensions["P"].width == 15  # block_scale_y
        assert ws.column_dimensions["S"].width == 40  # block_vertical_segments
        assert ws.column_dimensions["T"].width == 40  # block_horizontal_segments
        assert ws.column_dimensions["AC"].width == 20  # block_filtered_polygon_count

    def test_format_all_blocks_frozen_panes(self) -> None:
        """Test that frozen panes are applied at B2 (header row and first column)."""
        wb, ws = self._create_test_workbook_with_headers()

        _format_all_blocks_sheet(wb)

        assert ws.freeze_panes == "B2"

    def test_format_all_blocks_red_highlighting_varies_negative(self) -> None:
        """Test that rows with VARIES (-) get red highlighting."""
        wb, ws = self._create_test_workbook_with_headers()

        # Add a row with VARIES (-) in x_scale (column O = 15)
        ws.append(
            [
                "VALVE",
                "VALVE",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                "VARIES (-)",  # x_scale
                1.0,  # y_scale
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
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

        # Add a row with negative y_scale (column P = 16)
        ws.append(
            [
                "PIPE",
                "PIPE",
                "Inserted",
                False,
                "",
                12,
                5,
                1,
                "Layer1",
                3,
                0,
                2,
                0,
                0,
                1.0,  # x_scale
                -1.0,  # y_scale (negative)
                200.0,
                100.0,
                "20, 160, 20",
                "10, 80, 10",
                20.0,
                20.0,
                10.0,
                10.0,
                "TRUE",
                160.0,
                80.0,
                2,
                2,
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

        # Add a row with VARIES in x_scale (column O = 15)
        ws.append(
            [
                "BLOCK1",
                "BLOCK1",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                "VARIES",  # x_scale (positive variance)
                1.0,  # y_scale
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
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
                "BLOCK2",
                "BLOCK2",
                "Inserted",
                False,
                "",
                8,
                10,
                1,
                "Layer1",
                10,
                0,
                0,
                0,
                0,
                1.0,  # x_scale (positive)
                1.5,  # y_scale (positive)
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
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
                "VALVE",
                "VALVE",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                "VARIES (-)",
                1.0,
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
            ]
        )

        _format_all_blocks_sheet(wb)

        # All 29 columns of row 2 should have red fill
        for col_idx in range(1, 30):
            cell_fill = ws.cell(row=2, column=col_idx).fill
            assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
            assert cell_fill.fill_type == "solid"

    def test_format_all_blocks_segment_columns_right_aligned(self) -> None:
        """Test that segment columns (S and T) are right-aligned."""
        wb, ws = self._create_test_workbook_with_headers()

        ws.append(
            [
                "VALVE",
                "VALVE",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                1.0,
                1.0,
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
            ]
        )

        _format_all_blocks_sheet(wb)

        # Column S (19 = vertical_segments) should be right-aligned
        assert ws.cell(row=2, column=19).alignment.horizontal == "right"
        # Column T (20 = horizontal_segments) should be right-aligned
        assert ws.cell(row=2, column=20).alignment.horizontal == "right"

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
                "MIXED",
                "MIXED",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                "VARIES (-)",  # x_scale - should trigger red
                "VARIES",  # y_scale - would trigger yellow but red wins
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
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
                "BLOCK_Y",
                "BLOCK_Y",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                1.0,  # x_scale
                "VARIES (-)",  # y_scale
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
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
                "BLOCK_NEG_X",
                "BLOCK_NEG_X",
                "Inserted",
                False,
                "",
                8,
                10,
                2,
                "Layer1, Layer2",
                5,
                2,
                0,
                0,
                0,
                -1.0,  # x_scale (negative)
                1.0,  # y_scale (positive)
                100.0,
                50.0,
                "10, 80, 10",
                "5, 40, 5",
                10.0,
                10.0,
                5.0,
                5.0,
                "TRUE",
                80.0,
                40.0,
                2,
                2,
            ]
        )

        _format_all_blocks_sheet(wb)

        # Row 2 should have orange fill
        cell_fill = ws.cell(row=2, column=1).fill
        assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE
