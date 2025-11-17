"""
Application-wide constants for the DWG Block Extractor.

This module defines all constants used throughout the application including:
- Supported file extensions for DWG/DXF files
- Excel output configuration (column names, worksheet name)
- User-facing messages for UI and error handling

Usage:
    from core.constants import SUPPORTED_EXTENSIONS, EXCEL_COLUMN_BLOCK_NAME
"""

# File extensions
SUPPORTED_EXTENSIONS: tuple[str, str] = ('.dwg', '.dxf')

# Excel configuration - Sheet names
EXCEL_SHEET_BLOCK_COUNTS: str = 'Block Counts'
EXCEL_SHEET_LAYER_ANALYSIS: str = 'Layer Analysis'
EXCEL_SHEET_ENTITY_SUMMARY: str = 'Entity Summary'

# Excel configuration - Block Counts sheet columns
EXCEL_COLUMN_BLOCK_NAME: str = 'Block Name'
EXCEL_COLUMN_COUNT: str = 'Insertion Count'
EXCEL_COLUMN_ENTITIES_IN_DEFINITION: str = 'Entities in Definition'

# Excel configuration - Layer Analysis sheet columns
EXCEL_COLUMN_LAYER_NAME: str = 'Layer Name'
EXCEL_COLUMN_INSERTIONS_ON_LAYER: str = 'Insertions on Layer'
EXCEL_COLUMN_ENTITIES_ON_LAYER: str = 'Entities on Layer'

# Excel configuration - Entity Summary sheet columns
EXCEL_COLUMN_ENTITY_TYPE: str = 'Entity Type'
EXCEL_COLUMN_TOTAL_COUNT: str = 'Total Count'

# UI messages
MSG_SELECT_FILE: str = 'Please select a DWG or DXF file'
MSG_PROCESSING: str = 'Processing...'
MSG_SUCCESS: str = 'Extraction complete'
MSG_ERROR_INVALID_FILE: str = 'Invalid or corrupted file'
MSG_ERROR_NO_BLOCKS: str = 'No blocks found in file'
MSG_ERROR_FILE_NOT_FOUND: str = 'File not found'
