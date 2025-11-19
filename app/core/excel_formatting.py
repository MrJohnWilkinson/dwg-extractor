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

from openpyxl.styles import Alignment, PatternFill
from openpyxl.workbook.workbook import Workbook

from .constants import (
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from .logger import setup_logger


logger = setup_logger(__name__)


def format_header(column_name: str) -> str:
    """
    Convert snake_case column names to Title Case with proper spacing for Excel display.

    This function transforms code-level snake_case identifiers into human-readable
    Excel column headers. It handles acronyms (DWG, DXF, CAD, ID) by keeping them
    uppercase instead of title-cased.

    Args:
        column_name: Snake_case column name (e.g., "block_insertion_count")

    Returns:
        Title Case formatted string with spaces (e.g., "Block Insertion Count")

    Examples:
        >>> format_header("block_name")
        'Block Name'
        >>> format_header("layer_block_insertion_count")
        'Layer Block Insertion Count'
        >>> format_header("block_rotation_0")
        'Block Rotation 0'
        >>> format_header("count")
        'Count'
        >>> format_header("")
        ''
    """
    if not column_name:
        return ""

    # Acronyms that should remain uppercase
    acronym_overrides = {
        "Dwg": "DWG",
        "Dxf": "DXF",
        "Cad": "CAD",
        "Id": "ID",
    }

    # Split on underscores and convert to title case
    words = column_name.split("_")
    title_words = [word.title() for word in words]

    # Apply acronym overrides
    final_words = [acronym_overrides.get(word, word) for word in title_words]

    return " ".join(final_words)


def _format_block_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Analysis sheet (simplified inventory)."""
    ws = wb[EXCEL_SHEET_BLOCK_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row
    ws.freeze_panes = "A2"
    logger.info("Frozen panes applied to Block Analysis sheet")

    # Set column widths (5 columns)
    ws.column_dimensions["A"].width = 30  # block_name
    ws.column_dimensions["B"].width = 25  # block_insertion_count
    ws.column_dimensions["C"].width = 25  # block_entity_count
    ws.column_dimensions["D"].width = 25  # block_layer_name
    ws.column_dimensions["E"].width = 30  # block_xdata_apps

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    logger.info("Block Analysis sheet formatted")


def _format_layer_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Layer Analysis sheet."""
    ws = wb[EXCEL_SHEET_LAYER_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row
    ws.freeze_panes = "A2"
    logger.info("Frozen panes applied to Layer Analysis sheet")

    # Set column widths
    ws.column_dimensions["A"].width = 30  # layer_name
    ws.column_dimensions["B"].width = 25  # layer_block_insertion_count
    ws.column_dimensions["C"].width = 25  # layer_entity_count

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    logger.info("Layer Analysis sheet formatted")


def _format_entity_summary_sheet(wb: Workbook) -> None:
    """Apply formatting to the Entity Summary sheet."""
    ws = wb[EXCEL_SHEET_ENTITY_SUMMARY]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row
    ws.freeze_panes = "A2"
    logger.info("Frozen panes applied to Entity Summary sheet")

    # Set column widths
    ws.column_dimensions["A"].width = 25  # entity_type_name
    ws.column_dimensions["B"].width = 25  # entity_type_count

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    logger.info("Entity Summary sheet formatted")


def _format_block_geometry_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Geometry Analysis sheet with yellow highlighting for scale variance."""
    ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row
    ws.freeze_panes = "A2"
    logger.info("Frozen panes applied to Block Geometry Analysis sheet")

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

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    # Apply yellow highlighting to rows with "VARIES" in scale columns
    yellow_fill = PatternFill(
        start_color="FFFFFF00", end_color="FFFFFF00", fill_type="solid"
    )
    highlighted_rows = 0

    # Iterate through data rows (skip header at row 1)
    for row_idx in range(2, ws.max_row + 1):
        # Get scale values from columns H (x_scale) and I (y_scale)
        x_scale_cell = ws.cell(row=row_idx, column=8)  # Column H
        y_scale_cell = ws.cell(row=row_idx, column=9)  # Column I

        # Check if either scale contains "VARIES"
        x_scale = x_scale_cell.value
        y_scale = y_scale_cell.value

        if (x_scale == "VARIES") or (y_scale == "VARIES"):
            # Apply yellow fill to entire row (columns A-M)
            for col_idx in range(1, 14):  # Columns A through M
                ws.cell(row=row_idx, column=col_idx).fill = yellow_fill
            highlighted_rows += 1

    logger.info(
        f"Block Geometry Analysis sheet formatted with {highlighted_rows} rows highlighted for scale variance"
    )
