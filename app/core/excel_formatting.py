"""
Excel worksheet formatting utilities for CAD analysis reports.

This module provides functions for applying auto-filters, column widths, and conditional
formatting to Excel sheets. These utilities support the creation of professional, readable
Excel reports with proper visual presentation.

Usage:
    from core.excel_formatting import _format_block_analysis_sheet

    wb = load_workbook(excel_path)
    _format_block_analysis_sheet(wb)
    wb.save(excel_path)
"""

from openpyxl.styles import PatternFill
from openpyxl.workbook.workbook import Workbook

from .constants import (
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from .logger import setup_logger


logger = setup_logger(__name__)


def _format_block_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Analysis sheet (simplified inventory)."""
    ws = wb[EXCEL_SHEET_BLOCK_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths (4 columns only)
    ws.column_dimensions["A"].width = 30  # block_name
    ws.column_dimensions["B"].width = 25  # block_insertion_count
    ws.column_dimensions["C"].width = 25  # block_entity_count
    ws.column_dimensions["D"].width = 25  # block_layer_name

    logger.info("Block Analysis sheet formatted")


def _format_layer_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Layer Analysis sheet."""
    ws = wb[EXCEL_SHEET_LAYER_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions["A"].width = 30  # layer_name
    ws.column_dimensions["B"].width = 25  # layer_block_insertion_count
    ws.column_dimensions["C"].width = 25  # layer_entity_count

    logger.info("Layer Analysis sheet formatted")


def _format_entity_summary_sheet(wb: Workbook) -> None:
    """Apply formatting to the Entity Summary sheet."""
    ws = wb[EXCEL_SHEET_ENTITY_SUMMARY]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions["A"].width = 25  # entity_type_name
    ws.column_dimensions["B"].width = 25  # entity_type_count

    logger.info("Entity Summary sheet formatted")


def _format_block_geometry_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Geometry Analysis sheet with red highlighting for mirrored blocks."""
    ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths (13 columns)
    ws.column_dimensions["A"].width = 30  # block_name
    ws.column_dimensions["B"].width = 25  # block_layer_name
    ws.column_dimensions["C"].width = 12  # block_rotation_0
    ws.column_dimensions["D"].width = 12  # block_rotation_90
    ws.column_dimensions["E"].width = 12  # block_rotation_180
    ws.column_dimensions["F"].width = 12  # block_rotation_270
    ws.column_dimensions["G"].width = 12  # block_rotation_other
    ws.column_dimensions["H"].width = 15  # block_scale_x
    ws.column_dimensions["I"].width = 15  # block_scale_y
    ws.column_dimensions["J"].width = 20  # block_native_width
    ws.column_dimensions["K"].width = 20  # block_native_height
    ws.column_dimensions["L"].width = 40  # block_vertical_segments
    ws.column_dimensions["M"].width = 40  # block_horizontal_segments

    # Apply red highlighting to rows with negative scales (mirrored blocks)
    red_fill = PatternFill(
        start_color="FFFF0000", end_color="FFFF0000", fill_type="solid"
    )
    highlighted_rows = 0

    # Iterate through data rows (skip header at row 1)
    for row_idx in range(2, ws.max_row + 1):
        # Get scale values from columns H (x_scale) and I (y_scale)
        x_scale_cell = ws.cell(row=row_idx, column=8)  # Column H
        y_scale_cell = ws.cell(row=row_idx, column=9)  # Column I

        # Check if either scale is negative
        x_scale = x_scale_cell.value
        y_scale = y_scale_cell.value

        if (
            x_scale is not None and isinstance(x_scale, (int, float)) and x_scale < 0
        ) or (
            y_scale is not None and isinstance(y_scale, (int, float)) and y_scale < 0
        ):
            # Apply red fill to entire row (columns A-M)
            for col_idx in range(1, 14):  # Columns A through M
                ws.cell(row=row_idx, column=col_idx).fill = red_fill
            highlighted_rows += 1

    logger.info(
        f"Block Geometry Analysis sheet formatted with {highlighted_rows} rows highlighted for mirrored blocks"
    )
