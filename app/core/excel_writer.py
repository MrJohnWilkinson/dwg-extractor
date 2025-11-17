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
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_COUNT,
    EXCEL_COLUMN_ENTITIES_IN_DEFINITION,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_INSERTIONS_ON_LAYER,
    EXCEL_COLUMN_ENTITIES_ON_LAYER,
    EXCEL_COLUMN_ENTITY_TYPE,
    EXCEL_COLUMN_TOTAL_COUNT
)

logger = setup_logger(__name__)


def write_excel(extraction_data: ExtractionResult, output_path: str) -> str:
    """
    Generate a multi-sheet Excel file from comprehensive CAD extraction data.

    This function creates an Excel workbook with three sheets:
    - Block Counts: Block names with insertion counts and entity counts in definitions
    - Layer Analysis: Layers with insertion counts and entity counts
    - Entity Summary: Entity types with total counts

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

        # Load workbook for post-processing (formatting)
        wb = load_workbook(full_path)

        # Apply formatting to all sheets
        _format_block_counts_sheet(wb)
        _format_layer_analysis_sheet(wb)
        _format_entity_summary_sheet(wb)

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
    """Create the Block Counts sheet with block insertion and entity counts."""
    logger.info("Creating Block Counts sheet...")

    block_counts = data['block_counts']
    block_entities = data['block_entities']

    if block_counts:
        # Merge block_counts and block_entities into single DataFrame
        rows = []
        for block_name, insertion_count in block_counts.items():
            entity_count = block_entities.get(block_name, 0)
            rows.append({
                EXCEL_COLUMN_BLOCK_NAME: block_name,
                EXCEL_COLUMN_COUNT: insertion_count,
                EXCEL_COLUMN_ENTITIES_IN_DEFINITION: entity_count
            })

        df = pd.DataFrame(rows)
        df.sort_values(by=EXCEL_COLUMN_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_COUNT,
            EXCEL_COLUMN_ENTITIES_IN_DEFINITION
        ])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_COUNTS, index=False)
    logger.info(f"Block Counts sheet created with {len(df)} rows")


def _create_layer_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Layer Analysis sheet with layer-based metrics."""
    logger.info("Creating Layer Analysis sheet...")

    layer_insertions = data['layer_insertions']
    layer_entities = data['layer_entities']

    if layer_entities:
        # Merge layer data into single DataFrame
        rows = []
        for layer_name, entity_count in layer_entities.items():
            insertion_count = layer_insertions.get(layer_name, 0)
            rows.append({
                EXCEL_COLUMN_LAYER_NAME: layer_name,
                EXCEL_COLUMN_INSERTIONS_ON_LAYER: insertion_count,
                EXCEL_COLUMN_ENTITIES_ON_LAYER: entity_count
            })

        df = pd.DataFrame(rows)
        df.sort_values(by=EXCEL_COLUMN_ENTITIES_ON_LAYER, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[
            EXCEL_COLUMN_LAYER_NAME,
            EXCEL_COLUMN_INSERTIONS_ON_LAYER,
            EXCEL_COLUMN_ENTITIES_ON_LAYER
        ])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS, index=False)
    logger.info(f"Layer Analysis sheet created with {len(df)} rows")


def _create_entity_summary_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    """Create the Entity Summary sheet with global entity type counts."""
    logger.info("Creating Entity Summary sheet...")

    entity_types = data['entity_types']

    if entity_types:
        # Convert entity types to DataFrame
        df = pd.DataFrame(list(entity_types.items()),
                         columns=[EXCEL_COLUMN_ENTITY_TYPE, EXCEL_COLUMN_TOTAL_COUNT])
        df.sort_values(by=EXCEL_COLUMN_TOTAL_COUNT, ascending=False, inplace=True)
    else:
        # Create empty DataFrame with headers only
        df = pd.DataFrame(columns=[EXCEL_COLUMN_ENTITY_TYPE, EXCEL_COLUMN_TOTAL_COUNT])

    df.to_excel(writer, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY, index=False)
    logger.info(f"Entity Summary sheet created with {len(df)} rows")


def _format_block_counts_sheet(wb: Workbook) -> None:
    """Apply formatting to the Block Counts sheet."""
    ws = wb[EXCEL_SHEET_BLOCK_COUNTS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 30  # Block Name
    ws.column_dimensions['B'].width = 20  # Insertion Count
    ws.column_dimensions['C'].width = 25  # Entities in Definition

    logger.info("Block Counts sheet formatted")


def _format_layer_analysis_sheet(wb: Workbook) -> None:
    """Apply formatting to the Layer Analysis sheet."""
    ws = wb[EXCEL_SHEET_LAYER_ANALYSIS]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 30  # Layer Name
    ws.column_dimensions['B'].width = 20  # Insertions on Layer
    ws.column_dimensions['C'].width = 20  # Entities on Layer

    logger.info("Layer Analysis sheet formatted")


def _format_entity_summary_sheet(wb: Workbook) -> None:
    """Apply formatting to the Entity Summary sheet."""
    ws = wb[EXCEL_SHEET_ENTITY_SUMMARY]

    # Apply auto-filter
    if ws.dimensions:
        ws.auto_filter.ref = ws.dimensions

    # Set column widths
    ws.column_dimensions['A'].width = 25  # Entity Type
    ws.column_dimensions['B'].width = 20  # Total Count

    logger.info("Entity Summary sheet formatted")
