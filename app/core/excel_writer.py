"""
Excel file generation for the DWG Block Extractor.

This module provides functionality to convert comprehensive CAD analysis data into
multi-sheet Excel workbooks with proper sorting, auto-filtering, and column widths.

Usage:
    from core.excel_writer import write_excel
    from core.extractor import ExtractionResult

    result: ExtractionResult = extract_blocks('/path/to/drawing.dwg')
    excel_path = write_excel(result, '/path/to/drawing.dwg')
    # Returns: '/path/to/drawing_blocks_20250117_143022.xlsx'
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from openpyxl.utils import get_column_letter

from .logger import setup_logger
from .extractor import ExtractionResult
from .constants import (
    EXCEL_SHEET_BLOCK_COUNTS,
    EXCEL_SHEET_LAYER_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_LAYER_INSERTION_COUNT,
    EXCEL_COLUMN_LAYER_ENTITY_COUNT,
    EXCEL_COLUMN_ENTITY_TYPE_NAME,
    EXCEL_COLUMN_ENTITY_TYPE_COUNT
)

logger = setup_logger(__name__)


def write_excel(extraction_data: ExtractionResult, output_path: str) -> str:
    """
    Generate a multi-sheet Excel file from comprehensive CAD extraction data.

    This function creates an Excel workbook with four sheets:
    - Block Counts: Block-layer pairs with insertion counts and entity counts in definitions
    - Layer Analysis: Layers with insertion counts and entity counts
    - Entity Summary: Entity types with total counts
    - Block Trimming Analysis: Block geometry analysis with native dimensions and segments

    All sheets include headers, descending sort, auto-filters, and proper column widths.
    The output filename is timestamped to prevent overwrites.

    Args:
        extraction_data: ExtractionResult TypedDict containing all CAD analysis data
        output_path: Path to the original DWG/DXF file (used for output filename)

    Returns:
        Full path to the created Excel file as a string

    Raises:
        ValueError: If extraction_data is None or invalid

    Examples:
        >>> result = extract_blocks('drawing.dwg')
        >>> excel_file = write_excel(result, 'drawing.dwg')
        >>> print(excel_file)
        '/path/to/drawing_blocks_20250117_143022.xlsx'
    """
    logger.info("Starting multi-sheet Excel file generation")

    # Validate input
    if extraction_data is None:
        logger.error("extraction_data cannot be None")
        raise ValueError("extraction_data cannot be None")

    try:
        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = Path(output_path)
        filename = f"{input_path.stem}_blocks_{timestamp}.xlsx"
        full_path = input_path.parent / filename

        # Create Excel writer
        with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
            # Sheet 1: Block Counts
            _create_block_counts_sheet(extraction_data, writer)

            # Sheet 2: Layer Analysis
            _create_layer_analysis_sheet(extraction_data, writer)

            # Sheet 3: Entity Summary
            _create_entity_summary_sheet(extraction_data, writer)

            # Sheet 4: Block Trimming Analysis
            _create_block_trimming_analysis_sheet(extraction_data, writer)

        # Load workbook for post-processing (formatting)
        wb = load_workbook(full_path)

        # Apply formatting to all sheets
        _format_block_counts_sheet(wb)
        _format_layer_analysis_sheet(wb)
        _format_entity_summary_sheet(wb)
        _format_block_trimming_analysis_sheet(wb)

        # Save workbook with formatting
        wb.save(full_path)

        logger.info(f"Multi-sheet Excel file created successfully at {full_path}")
        return str(full_path)

    except ValueError as e:
        logger.error(f"Invalid input data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Excel generation: {str(e)}", exc_info=True)
        raise


def _create_block_counts_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Block Counts sheet with block-layer pairs, insertion counts, entity counts, and rotation breakdowns."""
    logger.info("Creating Block Counts sheet...")

    block_layer_pairs = data['block_layer_pairs']
    block_entities = data['block_entities']
    block_rotation_counts = data['block_rotation_counts']

    if block_layer_pairs:
        # Unpack block-layer pairs into DataFrame rows with rotation breakdowns
        rows = []
        for (block_name, layer_name), insertion_count in block_layer_pairs.items():
            entity_count = block_entities.get(block_name, 0)

            # Calculate rotation counts for this block-layer pair
            rot_0 = block_rotation_counts.get((block_name, layer_name, '0'), 0)
            rot_90 = block_rotation_counts.get((block_name, layer_name, '90'), 0)
            rot_180 = block_rotation_counts.get((block_name, layer_name, '180'), 0)
            rot_270 = block_rotation_counts.get((block_name, layer_name, '270'), 0)
            rot_other = block_rotation_counts.get((block_name, layer_name, 'other'), 0)

            rows.append({
                EXCEL_COLUMN_BLOCK_NAME: block_name,
                EXCEL_COLUMN_BLOCK_INSERTION_COUNT: insertion_count,
                EXCEL_COLUMN_BLOCK_ENTITY_COUNT: entity_count,
                EXCEL_COLUMN_BLOCK_LAYER_NAME: layer_name,
                EXCEL_COLUMN_BLOCK_ROTATION_0: rot_0,
                EXCEL_COLUMN_BLOCK_ROTATION_90: rot_90,
                EXCEL_COLUMN_BLOCK_ROTATION_180: rot_180,
                EXCEL_COLUMN_BLOCK_ROTATION_270: rot_270,
                EXCEL_COLUMN_BLOCK_ROTATION_OTHER: rot_other
            })

        df = pd.DataFrame(rows)
        df.sort_values(by=EXCEL_COLUMN_BLOCK_INSERTION_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only (all 9 columns)
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
            EXCEL_COLUMN_BLOCK_LAYER_NAME,
            EXCEL_COLUMN_BLOCK_ROTATION_0,
            EXCEL_COLUMN_BLOCK_ROTATION_90,
            EXCEL_COLUMN_BLOCK_ROTATION_180,
            EXCEL_COLUMN_BLOCK_ROTATION_270,
            EXCEL_COLUMN_BLOCK_ROTATION_OTHER
        ])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_COUNTS, index=False)
    logger.info(f"Block Counts sheet created with {len(df)} rows")


def _create_layer_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Layer Analysis sheet with layer-based metrics."""
    logger.info("Creating Layer Analysis sheet...")

    layer_insertion_counts = data['layer_insertion_counts']
    layer_entity_counts = data['layer_entity_counts']

    if layer_entity_counts:
        # Merge layer data into single DataFrame
        rows = []
        for layer_name, entity_count in layer_entity_counts.items():
            insertion_count = layer_insertion_counts.get(layer_name, 0)
            rows.append({
                EXCEL_COLUMN_LAYER_NAME: layer_name,
                EXCEL_COLUMN_LAYER_INSERTION_COUNT: insertion_count,
                EXCEL_COLUMN_LAYER_ENTITY_COUNT: entity_count
            })

        df = pd.DataFrame(rows)
        df.sort_values(by=EXCEL_COLUMN_LAYER_ENTITY_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_LAYER_NAME,
            EXCEL_COLUMN_LAYER_INSERTION_COUNT,
            EXCEL_COLUMN_LAYER_ENTITY_COUNT
        ])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS, index=False)
    logger.info(f"Layer Analysis sheet created with {len(df)} rows")


def _create_entity_summary_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Entity Summary sheet with global entity type counts."""
    logger.info("Creating Entity Summary sheet...")

    entity_type_counts = data['entity_type_counts']

    if entity_type_counts:
        # Convert entity types to DataFrame
        df = pd.DataFrame(list(entity_type_counts.items()),
                         columns=[EXCEL_COLUMN_ENTITY_TYPE_NAME, EXCEL_COLUMN_ENTITY_TYPE_COUNT])
        df.sort_values(by=EXCEL_COLUMN_ENTITY_TYPE_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[EXCEL_COLUMN_ENTITY_TYPE_NAME, EXCEL_COLUMN_ENTITY_TYPE_COUNT])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY, index=False)
    logger.info(f"Entity Summary sheet created with {len(df)} rows")


def _format_block_counts_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Counts sheet with rotation columns."""
    ws = wb[EXCEL_SHEET_BLOCK_COUNTS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 30  # block_name
    ws.column_dimensions['B'].width = 25  # block_insertion_count
    ws.column_dimensions['C'].width = 25  # block_entity_count
    ws.column_dimensions['D'].width = 25  # block_layer_name
    ws.column_dimensions['E'].width = 12  # block_rotation_0
    ws.column_dimensions['F'].width = 12  # block_rotation_90
    ws.column_dimensions['G'].width = 12  # block_rotation_180
    ws.column_dimensions['H'].width = 12  # block_rotation_270
    ws.column_dimensions['I'].width = 12  # block_rotation_other

    logger.info("Block Counts sheet formatted")


def _format_layer_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Layer Analysis sheet."""
    ws = wb[EXCEL_SHEET_LAYER_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 30  # layer_name
    ws.column_dimensions['B'].width = 25  # layer_insertion_count
    ws.column_dimensions['C'].width = 25  # layer_entity_count

    logger.info("Layer Analysis sheet formatted")


def _format_entity_summary_sheet(wb: Workbook) -> None:
    """Apply formatting to the Entity Summary sheet."""
    ws = wb[EXCEL_SHEET_ENTITY_SUMMARY]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 25  # entity_type_name
    ws.column_dimensions['B'].width = 25  # entity_type_count

    logger.info("Entity Summary sheet formatted")


def _create_block_trimming_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Block Trimming Analysis sheet with block geometry analysis data."""
    logger.info("Creating Block Trimming Analysis sheet...")

    block_trimming_data = data['block_trimming_data']

    if block_trimming_data:
        # Build DataFrame rows from block trimming data
        rows = []
        for block_name, geometry_data in block_trimming_data.items():
            native_width = geometry_data['native_width']
            native_height = geometry_data['native_height']
            vertical_segments = geometry_data['vertical_segments']
            horizontal_segments = geometry_data['horizontal_segments']

            # Convert segment lists to comma-separated strings
            vertical_segments_str = ", ".join(map(str, vertical_segments)) if vertical_segments else ""
            horizontal_segments_str = ", ".join(map(str, horizontal_segments)) if horizontal_segments else ""

            rows.append({
                EXCEL_COLUMN_BLOCK_NAME: block_name,
                EXCEL_COLUMN_BLOCK_NATIVE_WIDTH: native_width,
                EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT: native_height,
                EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS: vertical_segments_str,
                EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS: horizontal_segments_str
            })

        df = pd.DataFrame(rows)
        # Sort by block_name alphabetically
        df.sort_values(by=EXCEL_COLUMN_BLOCK_NAME, ascending=True, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
            EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
            EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
            EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS
        ])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS, index=False)
    logger.info(f"Block Trimming Analysis sheet created with {len(df)} rows")


def _format_block_trimming_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Trimming Analysis sheet."""
    ws = wb[EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 30  # block_name
    ws.column_dimensions['B'].width = 20  # block_native_width
    ws.column_dimensions['C'].width = 20  # block_native_height
    ws.column_dimensions['D'].width = 40  # block_vertical_segments
    ws.column_dimensions['E'].width = 40  # block_horizontal_segments

    logger.info("Block Trimming Analysis sheet formatted")
