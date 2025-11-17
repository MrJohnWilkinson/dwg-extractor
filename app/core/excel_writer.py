"""
Excel file generation for the DWG Block Extractor.

This module provides functionality to convert block count data into formatted
Excel spreadsheets with proper sorting, auto-filtering, and column widths.

Usage:
    from core.excel_writer import write_excel

    block_data = {'VALVE_GATE': 10, 'PIPE_SUPPORT': 5}
    excel_path = write_excel(block_data, '/path/to/drawing.dwg')
    # Returns: '/path/to/drawing_blocks_20250117_143022.xlsx'
"""

from pathlib import Path
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from .logger import setup_logger
from .constants import EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT, EXCEL_WORKSHEET_NAME

logger = setup_logger(__name__)


def write_excel(block_data: dict[str, int], output_path: str) -> str:
    """
    Generate an Excel file from block count data.

    This function converts a dictionary of block counts into a formatted Excel
    spreadsheet with headers, descending sort by count, auto-filter, and proper
    column widths. The output filename is timestamped to prevent overwrites.

    Args:
        block_data: Dictionary mapping block names to insertion counts
        output_path: Path to the original DWG/DXF file (used for output filename)

    Returns:
        Full path to the created Excel file as a string

    Raises:
        ValueError: If block_data is None or invalid

    Examples:
        >>> data = {'VALVE_GATE': 142, 'PIPE_SUPPORT': 89}
        >>> excel_file = write_excel(data, 'drawing.dwg')
        >>> print(excel_file)
        '/path/to/drawing_blocks_20250117_143022.xlsx'
    """
    logger.info(f"Starting Excel file generation with {len(block_data) if block_data else 0} unique blocks")

    # Validate input
    if block_data is None:
        logger.error("block_data cannot be None")
        raise ValueError("block_data cannot be None")

    # Handle empty block data
    if not block_data:
        logger.warning("No block data provided - creating Excel with headers only")

    try:
        # Convert dictionary to DataFrame
        if block_data:
            df = pd.DataFrame(list(block_data.items()),
                            columns=[EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT])
            # Sort by count descending
            df.sort_values(by=EXCEL_COLUMN_COUNT, ascending=False, inplace=True)
        else:
            # Create empty DataFrame with headers only
            df = pd.DataFrame(columns=[EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT])

        # Generate timestamped filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        input_path = Path(output_path)
        filename = f"{input_path.stem}_blocks_{timestamp}.xlsx"
        full_path = input_path.parent / filename

        # Write Excel file
        df.to_excel(full_path, sheet_name=EXCEL_WORKSHEET_NAME, index=False, engine='openpyxl')

        # Load workbook for post-processing
        wb = load_workbook(full_path)
        ws = wb[EXCEL_WORKSHEET_NAME]

        # Apply auto-filter
        if ws.dimensions:
            ws.auto_filter.ref = ws.dimensions

        # Adjust column widths
        # Column A (Block Name) - 30 characters
        ws.column_dimensions['A'].width = 30
        # Column B (Insertion Count) - 15 characters
        ws.column_dimensions['B'].width = 15

        # Save workbook with formatting
        wb.save(full_path)

        logger.info(f"Excel file created successfully at {full_path}")
        return str(full_path)

    except ValueError as e:
        logger.error(f"Invalid input data: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during Excel generation: {str(e)}", exc_info=True)
        raise
