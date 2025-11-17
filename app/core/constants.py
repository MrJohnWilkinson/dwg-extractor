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
SUPPORTED_EXTENSIONS = ('.dwg', '.dxf')

# Excel configuration
EXCEL_COLUMN_BLOCK_NAME = 'Block Name'
EXCEL_COLUMN_COUNT = 'Insertion Count'
EXCEL_WORKSHEET_NAME = 'Block Summary'

# UI messages
MSG_SELECT_FILE = 'Please select a DWG or DXF file'
MSG_PROCESSING = 'Processing...'
MSG_SUCCESS = 'Extraction complete'
MSG_ERROR_INVALID_FILE = 'Invalid or corrupted file'
MSG_ERROR_NO_BLOCKS = 'No blocks found in file'
MSG_ERROR_FILE_NOT_FOUND = 'File not found'
