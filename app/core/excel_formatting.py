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
    EXCEL_FILL_COLOR_EXTRACTION_ISSUE,
    EXCEL_FILL_COLOR_NESTED_BLOCK,
    EXCEL_FILL_COLOR_SCALE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
    EXCEL_SHEET_ALL_BLOCKS,
    EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_DEFINITIONS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_COLOR_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_EXTRACTION_ISSUES,
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

    # Freeze header row and first column
    ws.freeze_panes = "B2"
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

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Layer Analysis sheet")

    # Set column widths
    ws.column_dimensions["A"].width = 30  # layer_name
    ws.column_dimensions["B"].width = 25  # layer_block_insertion_count
    ws.column_dimensions["C"].width = 25  # layer_entity_count
    ws.column_dimensions["D"].width = 25  # layer_unique_color_count
    ws.column_dimensions["E"].width = 25  # layer_text_mtext_count

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    # Apply right-alignment to numeric columns (columns B, C, D, E - all data rows)
    right_alignment = Alignment(horizontal="right")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(
            row=row_idx, column=2
        ).alignment = right_alignment  # layer_block_insertion_count
        ws.cell(row=row_idx, column=3).alignment = right_alignment  # layer_entity_count
        ws.cell(
            row=row_idx, column=4
        ).alignment = right_alignment  # layer_unique_color_count
        ws.cell(
            row=row_idx, column=5
        ).alignment = right_alignment  # layer_text_mtext_count

    logger.info(
        "Layer Analysis sheet formatted with color and text/mtext count columns"
    )


def _format_entity_summary_sheet(wb: Workbook) -> None:
    """Apply formatting to the Entity Summary sheet."""
    ws = wb[EXCEL_SHEET_ENTITY_SUMMARY]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
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
    """Apply formatting to the Block Geometry Analysis sheet with three-tier scale highlighting."""
    ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
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
    ws.column_dimensions["N"].width = 12  # block_suggested_trim_left
    ws.column_dimensions["O"].width = 12  # block_suggested_trim_right
    ws.column_dimensions["P"].width = 12  # block_suggested_trim_top
    ws.column_dimensions["Q"].width = 12  # block_suggested_trim_bottom
    ws.column_dimensions["R"].width = 15  # block_content_zone_detected

    # Enable text wrapping on header row
    alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = alignment

    # Define three-tier highlighting fills
    red_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        fill_type="solid",
    )
    orange_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_NEGATIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_NEGATIVE,
        fill_type="solid",
    )
    yellow_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
        fill_type="solid",
    )

    # Track highlighting counts by color
    red_highlighted = 0
    orange_highlighted = 0
    yellow_highlighted = 0

    def _is_negative_number(value: object) -> bool:
        """Check if cell value is a negative number.

        Args:
            value: Cell value which can be various types (int, float, str, None,
                   Decimal, bool, date, time, etc. from openpyxl)

        Returns:
            True if value is a negative int or float, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value < 0
        # String values like "VARIES" or "VARIES (-)" and other types are not negative numbers
        return False

    # Iterate through data rows (skip header at row 1)
    for row_idx in range(2, ws.max_row + 1):
        # Get scale values from columns H (x_scale) and I (y_scale)
        x_scale_cell = ws.cell(row=row_idx, column=8)  # Column H
        y_scale_cell = ws.cell(row=row_idx, column=9)  # Column I

        x_scale = x_scale_cell.value
        y_scale = y_scale_cell.value

        # Determine highlight priority based on both X and Y scale values
        # Priority 1 (Red): "VARIES (-)" - variance with negative values
        # Priority 2 (Orange): Single negative number (e.g., -1.0)
        # Priority 3 (Yellow): "VARIES" - variance with all positive values
        # Priority 4 (None): No highlighting for consistent positive values

        fill_to_apply = None

        # Check for Priority 1: "VARIES (-)"
        if x_scale == "VARIES (-)" or y_scale == "VARIES (-)":
            fill_to_apply = red_fill
            red_highlighted += 1
        # Check for Priority 2: Negative number
        elif _is_negative_number(x_scale) or _is_negative_number(y_scale):
            fill_to_apply = orange_fill
            orange_highlighted += 1
        # Check for Priority 3: "VARIES"
        elif x_scale == "VARIES" or y_scale == "VARIES":
            fill_to_apply = yellow_fill
            yellow_highlighted += 1

        # Apply fill to entire row (columns A-M) if highlighting is needed
        if fill_to_apply is not None:
            for col_idx in range(1, 14):  # Columns A through M
                ws.cell(row=row_idx, column=col_idx).fill = fill_to_apply

    # Apply right-alignment to segment columns (L and M)
    right_alignment = Alignment(horizontal="right")
    for row_idx in range(2, ws.max_row + 1):
        # Column L (12) - block_vertical_segments
        l_cell = ws.cell(row=row_idx, column=12)
        l_cell.alignment = right_alignment

        # Column M (13) - block_horizontal_segments
        m_cell = ws.cell(row=row_idx, column=13)
        m_cell.alignment = right_alignment

    total_highlighted = red_highlighted + orange_highlighted + yellow_highlighted
    logger.info(
        f"Block Geometry Analysis sheet formatted with {total_highlighted} rows highlighted "
        f"(red: {red_highlighted}, orange: {orange_highlighted}, yellow: {yellow_highlighted}) "
        f"and segment columns right-aligned"
    )


def _format_annotations_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Annotations Analysis sheet with RGB color fills."""
    ws = wb[EXCEL_SHEET_ANNOTATIONS_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Annotations Analysis sheet")

    # Set column widths (8 columns: A-H)
    ws.column_dimensions["A"].width = 60  # annotation_contents
    ws.column_dimensions["B"].width = 15  # annotation_type
    ws.column_dimensions["C"].width = 25  # annotation_layer_name
    ws.column_dimensions["D"].width = 12  # annotation_color_r
    ws.column_dimensions["E"].width = 12  # annotation_color_g
    ws.column_dimensions["F"].width = 12  # annotation_color_b
    ws.column_dimensions["G"].width = 12  # annotation_color_sample
    ws.column_dimensions["H"].width = 20  # annotation_count

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Enable text wrapping on annotation_contents column (column A) for all data rows
    content_alignment = Alignment(wrap_text=True, vertical="top")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=1).alignment = content_alignment

    # Apply RGB color fills to annotation_color_sample column (column G)
    color_fills_applied = 0
    for row_idx in range(2, ws.max_row + 1):
        # Read RGB values from columns D, E, F
        r_value = ws.cell(row=row_idx, column=4).value
        g_value = ws.cell(row=row_idx, column=5).value
        b_value = ws.cell(row=row_idx, column=6).value

        # Validate RGB values
        if (
            isinstance(r_value, int)
            and isinstance(g_value, int)
            and isinstance(b_value, int)
            and 0 <= r_value <= 255
            and 0 <= g_value <= 255
            and 0 <= b_value <= 255
        ):
            # Convert RGB to hex format (RRGGBB)
            hex_color = f"{r_value:02X}{g_value:02X}{b_value:02X}"

            # Create and apply fill to column G (annotation_color_sample)
            color_fill = PatternFill(
                start_color=hex_color, end_color=hex_color, fill_type="solid"
            )
            ws.cell(row=row_idx, column=7).fill = color_fill
            color_fills_applied += 1

    logger.info(
        f"Annotations Analysis sheet formatted with {color_fills_applied} color sample cells filled"
    )


def _format_color_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Color Analysis sheet with RGB color fills."""
    ws = wb[EXCEL_SHEET_COLOR_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Color Analysis sheet")

    # Set column widths (9 columns: A-I)
    ws.column_dimensions["A"].width = 50  # color_annotation_contents
    ws.column_dimensions["B"].width = 20  # color_layer_name
    ws.column_dimensions["C"].width = 10  # color_red
    ws.column_dimensions["D"].width = 10  # color_green
    ws.column_dimensions["E"].width = 10  # color_blue
    ws.column_dimensions["F"].width = 12  # color_sample
    ws.column_dimensions["G"].width = 20  # color_autocad_name
    ws.column_dimensions["H"].width = 20  # color_entity_type
    ws.column_dimensions["I"].width = 15  # color_entity_count

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Enable text wrapping on annotation_contents column (column A) for all data rows
    content_alignment = Alignment(wrap_text=True, vertical="top")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=1).alignment = content_alignment

    # Apply right-alignment to numeric columns (C, D, E, I)
    right_alignment = Alignment(horizontal="right")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=3).alignment = right_alignment  # color_red
        ws.cell(row=row_idx, column=4).alignment = right_alignment  # color_green
        ws.cell(row=row_idx, column=5).alignment = right_alignment  # color_blue
        ws.cell(row=row_idx, column=9).alignment = right_alignment  # color_entity_count

    # Apply RGB color fills to color_sample column (column F)
    color_fills_applied = 0
    for row_idx in range(2, ws.max_row + 1):
        # Read RGB values from columns C, D, E
        r_value = ws.cell(row=row_idx, column=3).value
        g_value = ws.cell(row=row_idx, column=4).value
        b_value = ws.cell(row=row_idx, column=5).value

        # Validate RGB values
        if (
            isinstance(r_value, int)
            and isinstance(g_value, int)
            and isinstance(b_value, int)
            and 0 <= r_value <= 255
            and 0 <= g_value <= 255
            and 0 <= b_value <= 255
        ):
            # Convert RGB to hex format (RRGGBB)
            hex_color = f"{r_value:02X}{g_value:02X}{b_value:02X}"

            # Create and apply fill to column F (color_sample)
            color_fill = PatternFill(
                start_color=hex_color, end_color=hex_color, fill_type="solid"
            )
            ws.cell(row=row_idx, column=6).fill = color_fill
            color_fills_applied += 1

    logger.info(
        f"Color Analysis sheet formatted with {color_fills_applied} color sample cells filled"
    )


def _format_extraction_issues_sheet(wb: Workbook) -> None:
    """Apply formatting to the Extraction Issues sheet with yellow highlighting."""
    ws = wb[EXCEL_SHEET_EXTRACTION_ISSUES]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Extraction Issues sheet")

    # Set column widths (5 columns: A-E)
    ws.column_dimensions["A"].width = 30  # issue_type
    ws.column_dimensions["B"].width = 30  # issue_block_name
    ws.column_dimensions["C"].width = 25  # issue_layer_name
    ws.column_dimensions["D"].width = 20  # issue_insertion_count
    ws.column_dimensions["E"].width = 50  # issue_details

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Define yellow fill for issue rows
    yellow_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_EXTRACTION_ISSUE,
        end_color=EXCEL_FILL_COLOR_EXTRACTION_ISSUE,
        fill_type="solid",
    )

    # Apply yellow background fill to all data rows to highlight issues
    rows_highlighted = 0
    for row_idx in range(2, ws.max_row + 1):
        # Apply fill to entire row (columns A-E)
        for col_idx in range(1, 6):
            ws.cell(row=row_idx, column=col_idx).fill = yellow_fill
        rows_highlighted += 1

    # Apply right-alignment to insertion_count column (D)
    right_alignment = Alignment(horizontal="right")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=4).alignment = right_alignment

    # Enable text wrapping on details column (E) for all data rows
    details_alignment = Alignment(wrap_text=True, vertical="top")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=5).alignment = details_alignment

    logger.info(
        f"Extraction Issues sheet formatted with {rows_highlighted} rows highlighted"
    )


def _format_block_definitions_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Definitions sheet with green highlighting for nested blocks."""
    if EXCEL_SHEET_BLOCK_DEFINITIONS not in wb.sheetnames:
        logger.info("Block Definitions sheet not found, skipping formatting")
        return

    ws = wb[EXCEL_SHEET_BLOCK_DEFINITIONS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to Block Definitions sheet")

    # Set column widths (6 columns: A-F)
    ws.column_dimensions["A"].width = 30  # block_raw_name
    ws.column_dimensions["B"].width = 30  # block_resolved_name
    ws.column_dimensions["C"].width = 20  # block_insertion_status
    ws.column_dimensions["D"].width = 15  # block_is_nested
    ws.column_dimensions["E"].width = 40  # block_nested_parent_names
    ws.column_dimensions["F"].width = 20  # block_entity_count

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Define green fill for nested blocks
    green_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_NESTED_BLOCK,
        end_color=EXCEL_FILL_COLOR_NESTED_BLOCK,
        fill_type="solid",
    )

    # Apply green highlighting to rows where block_is_nested is True
    # Column D contains the is_nested boolean
    rows_highlighted = 0
    for row_idx in range(2, ws.max_row + 1):
        is_nested_value = ws.cell(row=row_idx, column=4).value
        if is_nested_value is True or is_nested_value == "True":
            # Apply fill to entire row (columns A-F)
            for col_idx in range(1, 7):
                ws.cell(row=row_idx, column=col_idx).fill = green_fill
            rows_highlighted += 1

    # Apply right-alignment to entity_count column (F)
    right_alignment = Alignment(horizontal="right")
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=6).alignment = right_alignment

    logger.info(
        f"Block Definitions sheet formatted with {rows_highlighted} nested block rows highlighted"
    )


def _format_all_blocks_sheet(wb: Workbook) -> None:
    """
    Apply formatting to the All Blocks sheet with scale highlighting.

    This function applies:
    - Auto-filter to the header row
    - Frozen panes (header row and first column)
    - Column widths appropriate for each data type
    - Text wrapping on header row
    - Three-tier scale highlighting:
      - Red: "VARIES (-)" - variance with negative values
      - Orange: Single negative number (e.g., -1.0)
      - Yellow: "VARIES" - variance with all positive values

    Args:
        wb: openpyxl Workbook object containing the All Blocks sheet
    """
    if EXCEL_SHEET_ALL_BLOCKS not in wb.sheetnames:
        logger.info("All Blocks sheet not found, skipping formatting")
        return

    ws = wb[EXCEL_SHEET_ALL_BLOCKS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Freeze header row and first column
    ws.freeze_panes = "B2"
    logger.info("Frozen panes applied to All Blocks sheet")

    # Set column widths (31 columns: A-AE)
    ws.column_dimensions["A"].width = 35  # block_raw_name
    ws.column_dimensions["B"].width = 35  # block_layer_names (MOVED here)
    ws.column_dimensions["C"].width = 35  # block_resolved_name
    ws.column_dimensions["D"].width = 12  # block_suggested_trim_left
    ws.column_dimensions["E"].width = 12  # block_suggested_trim_right
    ws.column_dimensions["F"].width = 12  # block_suggested_trim_top
    ws.column_dimensions["G"].width = 12  # block_suggested_trim_bottom
    ws.column_dimensions["H"].width = 50  # block_vertical_segments
    ws.column_dimensions["I"].width = 50  # block_horizontal_segments
    ws.column_dimensions["J"].width = 15  # block_native_width
    ws.column_dimensions["K"].width = 15  # block_native_height
    ws.column_dimensions["L"].width = 18  # block_content_zone_detected
    ws.column_dimensions["M"].width = 18  # block_content_zone_width
    ws.column_dimensions["N"].width = 18  # block_content_zone_height
    ws.column_dimensions["O"].width = 15  # block_polygon_count
    ws.column_dimensions["P"].width = 18  # block_filtered_polygon_count
    ws.column_dimensions["Q"].width = 18  # block_insertion_status
    ws.column_dimensions["R"].width = 12  # block_is_nested
    ws.column_dimensions["S"].width = 35  # block_nested_parent_names
    ws.column_dimensions["T"].width = 15  # block_entity_count
    ws.column_dimensions["U"].width = 18  # block_insertion_count
    ws.column_dimensions["V"].width = 12  # block_layer_count
    ws.column_dimensions["W"].width = 10  # block_rotation_0
    ws.column_dimensions["X"].width = 10  # block_rotation_90
    ws.column_dimensions["Y"].width = 10  # block_rotation_180
    ws.column_dimensions["Z"].width = 10  # block_rotation_270
    ws.column_dimensions["AA"].width = 12  # block_rotation_other
    ws.column_dimensions["AB"].width = 12  # block_scale_x
    ws.column_dimensions["AC"].width = 12  # block_scale_y
    ws.column_dimensions["AD"].width = 12  # block_attribute_count (NEW)
    ws.column_dimensions["AE"].width = 60  # block_attribute_data (NEW)

    # Enable text wrapping on header row
    header_alignment = Alignment(wrap_text=True, vertical="top")
    for cell in ws[1]:
        cell.alignment = header_alignment

    # Apply text wrapping for data rows in columns with potentially long text
    # Columns: A (raw_name), B (layer_names), C (resolved_name), H (vert_segments),
    #          I (horiz_segments), S (parent_names), AE (attribute_data)
    wrap_columns = [1, 2, 3, 8, 9, 19, 31]  # Column indices (1-based)
    wrap_alignment = Alignment(wrap_text=True, vertical="top")
    for row_idx in range(2, ws.max_row + 1):
        for col_idx in wrap_columns:
            ws.cell(row=row_idx, column=col_idx).alignment = wrap_alignment

    # Define three-tier highlighting fills
    red_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        fill_type="solid",
    )
    orange_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_NEGATIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_NEGATIVE,
        fill_type="solid",
    )
    yellow_fill = PatternFill(
        start_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
        end_color=EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
        fill_type="solid",
    )

    # Track highlighting counts by color
    red_highlighted = 0
    orange_highlighted = 0
    yellow_highlighted = 0

    def _is_negative_number(value: object) -> bool:
        """Check if cell value is a negative number.

        Args:
            value: Cell value which can be various types (int, float, str, None,
                   Decimal, bool, date, time, etc. from openpyxl)

        Returns:
            True if value is a negative int or float, False otherwise
        """
        if value is None:
            return False
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value < 0
        # String values like "VARIES" or "VARIES (-)" and other types are not negative numbers
        return False

    # Iterate through data rows (skip header at row 1)
    # Scale columns are AB (28 = x_scale) and AC (29 = y_scale)
    # Note: Column indices unchanged from pre-Unit-2; new columns AD/AE added after
    for row_idx in range(2, ws.max_row + 1):
        x_scale_cell = ws.cell(row=row_idx, column=28)  # Column AB
        y_scale_cell = ws.cell(row=row_idx, column=29)  # Column AC

        x_scale = x_scale_cell.value
        y_scale = y_scale_cell.value

        # Determine highlight priority based on both X and Y scale values
        # Priority 1 (Red): "VARIES (-)" - variance with negative values
        # Priority 2 (Orange): Single negative number (e.g., -1.0)
        # Priority 3 (Yellow): "VARIES" - variance with all positive values
        # Priority 4 (None): No highlighting for consistent positive values

        fill_to_apply = None

        # Check for Priority 1: "VARIES (-)"
        if x_scale == "VARIES (-)" or y_scale == "VARIES (-)":
            fill_to_apply = red_fill
            red_highlighted += 1
        # Check for Priority 2: Negative number
        elif _is_negative_number(x_scale) or _is_negative_number(y_scale):
            fill_to_apply = orange_fill
            orange_highlighted += 1
        # Check for Priority 3: "VARIES"
        elif x_scale == "VARIES" or y_scale == "VARIES":
            fill_to_apply = yellow_fill
            yellow_highlighted += 1

        # Apply fill to entire row (all 31 columns A-AE) if highlighting is needed
        if fill_to_apply is not None:
            for col_idx in range(1, 32):  # Columns A through AE (1-31)
                ws.cell(row=row_idx, column=col_idx).fill = fill_to_apply

    total_highlighted = red_highlighted + orange_highlighted + yellow_highlighted
    logger.info(
        f"All Blocks sheet formatted with {total_highlighted} rows highlighted "
        f"(red: {red_highlighted}, orange: {orange_highlighted}, yellow: {yellow_highlighted}) "
        f"and text wrapping applied to name/segment columns"
    )
