"""
Unit tests for the excel_writer module.

This test suite validates the Excel generation functionality including:
- Basic file creation with sample data
- Header column name verification
- Descending sort order validation
- Auto-filter presence confirmation
- Timestamped filename format verification
- Empty data handling (headers only)
- Column width formatting verification
"""

import pytest
from pathlib import Path
import pandas as pd
from openpyxl import load_workbook
import tempfile
import os
import re
from typing import Iterator

from core.excel_writer import write_excel
from core.constants import EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT, EXCEL_WORKSHEET_NAME


class TestExcelWriter:
    """Test suite for the write_excel function."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_block_data(self) -> dict[str, int]:
        """Provide sample block data for testing."""
        return {'VALVE': 10, 'PIPE': 5, 'TAG': 3}

    def test_write_excel_basic(self, temp_dir: str, sample_block_data: dict[str, int]) -> None:
        """Test basic Excel file creation."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')

        # Create the Excel file
        excel_path = write_excel(sample_block_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Verify it's a valid Excel file by loading it
        df = pd.read_excel(excel_path, sheet_name=EXCEL_WORKSHEET_NAME)
        assert df is not None
        assert len(df) == 3  # 3 rows of data

    def test_excel_has_headers(self, temp_dir: str, sample_block_data: dict[str, int]) -> None:
        """Test that Excel file has correct column headers."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_block_data, output_path)

        # Load and verify headers
        df = pd.read_excel(excel_path, sheet_name=EXCEL_WORKSHEET_NAME)
        assert list(df.columns) == [EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT]

    def test_excel_sorted_descending(self, temp_dir: str) -> None:
        """Test that Excel data is sorted by count in descending order."""
        unsorted_data = {'VALVE': 5, 'PIPE': 10, 'TAG': 3}
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(unsorted_data, output_path)

        # Load and verify sort order
        df = pd.read_excel(excel_path, sheet_name=EXCEL_WORKSHEET_NAME)

        # First row should have count=10 (PIPE)
        assert df.iloc[0][EXCEL_COLUMN_COUNT] == 10
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_NAME] == 'PIPE'

        # Second row should have count=5 (VALVE)
        assert df.iloc[1][EXCEL_COLUMN_COUNT] == 5

        # Last row should have count=3 (TAG)
        assert df.iloc[2][EXCEL_COLUMN_COUNT] == 3
        assert df.iloc[2][EXCEL_COLUMN_BLOCK_NAME] == 'TAG'

    def test_excel_autofilter(self, temp_dir: str, sample_block_data: dict[str, int]) -> None:
        """Test that auto-filter is applied to headers."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_block_data, output_path)

        # Load workbook with openpyxl
        wb = load_workbook(excel_path)
        ws = wb[EXCEL_WORKSHEET_NAME]

        # Verify auto-filter is set
        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref != ''

    def test_filename_format(self, temp_dir: str, sample_block_data: dict[str, int]) -> None:
        """Test that filename matches the expected timestamped pattern."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_block_data, output_path)

        # Verify filename pattern: test_drawing_blocks_YYYYMMDD_HHMMSS.xlsx
        filename = Path(excel_path).name
        pattern = r'test_drawing_blocks_\d{8}_\d{6}\.xlsx'
        assert re.match(pattern, filename), f"Filename '{filename}' doesn't match pattern"

        # Verify file exists at the returned path
        assert Path(excel_path).exists()

    def test_empty_data(self, temp_dir: str) -> None:
        """Test handling of empty block data."""
        empty_data: dict[str, int] = {}
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        # Verify file is created
        assert Path(excel_path).exists()

        # Load and verify it has headers but no data rows
        df = pd.read_excel(excel_path, sheet_name=EXCEL_WORKSHEET_NAME)
        assert len(df) == 0  # No data rows
        assert list(df.columns) == [EXCEL_COLUMN_BLOCK_NAME, EXCEL_COLUMN_COUNT]

    def test_column_widths(self, temp_dir: str, sample_block_data: dict[str, int]) -> None:
        """Test that column widths are set correctly."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_block_data, output_path)

        # Load workbook with openpyxl
        wb = load_workbook(excel_path)
        ws = wb[EXCEL_WORKSHEET_NAME]

        # Verify column widths
        assert ws.column_dimensions['A'].width == 30  # Block Name column
        assert ws.column_dimensions['B'].width == 15  # Insertion Count column

    def test_none_data_raises_error(self, temp_dir: str) -> None:
        """Test that None data raises ValueError."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')

        with pytest.raises(ValueError, match="block_data cannot be None"):
            write_excel(None, output_path)  # type: ignore[arg-type]

    def test_multiple_blocks(self, temp_dir: str) -> None:
        """Test with a larger dataset."""
        large_data = {
            'BLOCK_A': 100,
            'BLOCK_B': 50,
            'BLOCK_C': 75,
            'BLOCK_D': 25,
            'BLOCK_E': 60,
        }
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(large_data, output_path)

        # Load and verify
        df = pd.read_excel(excel_path, sheet_name=EXCEL_WORKSHEET_NAME)
        assert len(df) == 5

        # Verify sorted correctly (descending)
        assert df.iloc[0][EXCEL_COLUMN_COUNT] == 100  # BLOCK_A
        assert df.iloc[1][EXCEL_COLUMN_COUNT] == 75   # BLOCK_C
        assert df.iloc[2][EXCEL_COLUMN_COUNT] == 60   # BLOCK_E
        assert df.iloc[3][EXCEL_COLUMN_COUNT] == 50   # BLOCK_B
        assert df.iloc[4][EXCEL_COLUMN_COUNT] == 25   # BLOCK_D
