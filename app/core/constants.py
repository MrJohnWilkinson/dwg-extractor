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
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_BLOCK_NAME: str = 'block_name'
EXCEL_COLUMN_BLOCK_INSERTION_COUNT: str = 'block_insertion_count'
EXCEL_COLUMN_BLOCK_ENTITY_COUNT: str = 'block_entity_count'
EXCEL_COLUMN_BLOCK_LAYER_NAME: str = 'block_layer_name'  # See app_docs/005-field-naming-convention.md

# Excel configuration - Layer Analysis sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_LAYER_NAME: str = 'layer_name'
EXCEL_COLUMN_LAYER_INSERTION_COUNT: str = 'layer_insertion_count'
EXCEL_COLUMN_LAYER_ENTITY_COUNT: str = 'layer_entity_count'

# Excel configuration - Entity Summary sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_ENTITY_TYPE_NAME: str = 'entity_type_name'
EXCEL_COLUMN_ENTITY_TYPE_COUNT: str = 'entity_type_count'

# UI messages
MSG_SELECT_FILE: str = 'Please select a DWG or DXF file'
MSG_PROCESSING: str = 'Processing...'
MSG_SUCCESS: str = 'Extraction complete'
MSG_ERROR_INVALID_FILE: str = 'Invalid or corrupted file'
MSG_ERROR_NO_BLOCKS: str = 'No blocks found in file'
MSG_ERROR_FILE_NOT_FOUND: str = 'File not found'
