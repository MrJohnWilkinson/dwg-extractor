"""
Unit tests for the excel_writer module.

This test suite validates the multi-sheet Excel generation functionality including:
- Three-sheet workbook creation
- Correct headers on all sheets
- Data distribution across sheets
- Descending sort order on all sheets
- Auto-filter presence on all sheets
- Column width formatting on all sheets
- Timestamped filename format verification
- Empty data handling (headers only)
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
from core.extractor import ExtractionResult
from core.constants import (
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


class TestExcelWriter:
    """Test suite for the write_excel function."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_extraction_data(self) -> ExtractionResult:
        """Provide sample extraction data for testing."""
        return {
            'block_counts': {'VALVE': 10, 'PIPE': 5, 'TAG': 3},
            'block_entities': {'VALVE': 8, 'PIPE': 12, 'TAG': 4},
            'block_layer_pairs': {
                ('VALVE', 'Layer1'): 7,
                ('VALVE', 'Layer2'): 3,
                ('PIPE', 'Layer1'): 5,
                ('TAG', 'Layer1'): 3
            },
            'block_rotation_counts': {
                ('VALVE', 'Layer1', '0'): 5,
                ('VALVE', 'Layer1', '90'): 2,
                ('VALVE', 'Layer2', '0'): 3,
                ('PIPE', 'Layer1', '0'): 3,
                ('PIPE', 'Layer1', '180'): 2,
                ('TAG', 'Layer1', 'other'): 3
            },
            'layer_insertion_counts': {'Layer1': 15, 'Layer2': 3},
            'layer_entity_counts': {'Layer1': 25, 'Layer2': 10},
            'entity_type_counts': {'INSERT': 18, 'LINE': 15, 'CIRCLE': 8},
            'block_trimming_data': {
                'VALVE': {
                    'native_width': 100.0,
                    'native_height': 50.0,
                    'vertical_segments': [10.0, 80.0, 10.0],
                    'horizontal_segments': [5.0, 40.0, 5.0]
                },
                'PIPE': {
                    'native_width': 200.0,
                    'native_height': 100.0,
                    'vertical_segments': [20.0, 160.0, 20.0],
                    'horizontal_segments': [10.0, 80.0, 10.0]
                },
                'TAG': {
                    'native_width': 50.0,
                    'native_height': 25.0,
                    'vertical_segments': [50.0],
                    'horizontal_segments': [25.0]
                }
            }
        }

    def test_write_excel_four_sheets(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that four sheets are created with correct names."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load and verify sheet names
        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_BLOCK_COUNTS in wb.sheetnames
        assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS in wb.sheetnames
        assert len(wb.sheetnames) == 4

    def test_block_counts_sheet_structure(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Counts sheet has correct columns and data with block-layer pairs."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Counts sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_COUNTS)

        # Verify headers include block_layer_name and rotation columns
        assert list(df.columns) == [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
            EXCEL_COLUMN_BLOCK_LAYER_NAME,
            EXCEL_COLUMN_BLOCK_ROTATION_0,
            EXCEL_COLUMN_BLOCK_ROTATION_90,
            EXCEL_COLUMN_BLOCK_ROTATION_180,
            EXCEL_COLUMN_BLOCK_ROTATION_270,
            EXCEL_COLUMN_BLOCK_ROTATION_OTHER
        ]

        # Verify data rows (4 block-layer pairs)
        assert len(df) == 4
        # First row should be VALVE on Layer1 with 7 insertions
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_NAME] == 'VALVE'
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_INSERTION_COUNT] == 7
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_ENTITY_COUNT] == 8
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_LAYER_NAME] == 'Layer1'

    def test_layer_analysis_sheet_structure(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Layer Analysis sheet has correct columns and data."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Layer Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)

        # Verify headers
        assert list(df.columns) == [
            EXCEL_COLUMN_LAYER_NAME,
            EXCEL_COLUMN_LAYER_INSERTION_COUNT,
            EXCEL_COLUMN_LAYER_ENTITY_COUNT
        ]

        # Verify data rows
        assert len(df) == 2
        # Sorted by layer_entity_count descending
        assert df.iloc[0][EXCEL_COLUMN_LAYER_NAME] == 'Layer1'
        assert df.iloc[0][EXCEL_COLUMN_LAYER_ENTITY_COUNT] == 25

    def test_entity_summary_sheet_structure(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Entity Summary sheet has correct columns and data."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Entity Summary sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)

        # Verify headers
        assert list(df.columns) == [
            EXCEL_COLUMN_ENTITY_TYPE_NAME,
            EXCEL_COLUMN_ENTITY_TYPE_COUNT
        ]

        # Verify data rows
        assert len(df) == 3

    def test_all_sheets_sorted(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that all sheets are sorted correctly."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Block Counts: sorted by block_insertion_count descending
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_COUNTS)
        # First row should be VALVE/Layer1 with 7
        assert df_blocks.iloc[0][EXCEL_COLUMN_BLOCK_INSERTION_COUNT] == 7
        # Second row should be PIPE/Layer1 with 5
        assert df_blocks.iloc[1][EXCEL_COLUMN_BLOCK_INSERTION_COUNT] == 5
        # Third and fourth rows should both have 3
        assert df_blocks.iloc[2][EXCEL_COLUMN_BLOCK_INSERTION_COUNT] == 3

        # Layer Analysis: sorted by layer_entity_count descending
        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert df_layers.iloc[0][EXCEL_COLUMN_LAYER_ENTITY_COUNT] == 25  # Layer1
        assert df_layers.iloc[1][EXCEL_COLUMN_LAYER_ENTITY_COUNT] == 10  # Layer2

        # Entity Summary: sorted by entity_type_count descending
        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert df_entities.iloc[0][EXCEL_COLUMN_ENTITY_TYPE_COUNT] == 18  # INSERT
        assert df_entities.iloc[1][EXCEL_COLUMN_ENTITY_TYPE_COUNT] == 15  # LINE
        assert df_entities.iloc[2][EXCEL_COLUMN_ENTITY_TYPE_COUNT] == 8   # CIRCLE

    def test_all_sheets_autofilter(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that auto-filters are applied to all sheets."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify auto-filter on Block Counts sheet
        ws_blocks = wb[EXCEL_SHEET_BLOCK_COUNTS]
        assert ws_blocks.auto_filter.ref is not None

        # Verify auto-filter on Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.auto_filter.ref is not None

        # Verify auto-filter on Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.auto_filter.ref is not None

    def test_all_sheets_column_widths(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that column widths are set correctly on all sheets."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Block Counts sheet
        ws_blocks = wb[EXCEL_SHEET_BLOCK_COUNTS]
        assert ws_blocks.column_dimensions['A'].width == 30  # block_name
        assert ws_blocks.column_dimensions['B'].width == 25  # block_insertion_count
        assert ws_blocks.column_dimensions['C'].width == 25  # block_entity_count
        assert ws_blocks.column_dimensions['D'].width == 25  # block_layer_name
        assert ws_blocks.column_dimensions['E'].width == 12  # block_rotation_0
        assert ws_blocks.column_dimensions['F'].width == 12  # block_rotation_90
        assert ws_blocks.column_dimensions['G'].width == 12  # block_rotation_180
        assert ws_blocks.column_dimensions['H'].width == 12  # block_rotation_270
        assert ws_blocks.column_dimensions['I'].width == 12  # block_rotation_other

        # Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.column_dimensions['A'].width == 30  # layer_name
        assert ws_layers.column_dimensions['B'].width == 25  # layer_insertion_count
        assert ws_layers.column_dimensions['C'].width == 25  # layer_entity_count

        # Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.column_dimensions['A'].width == 25  # entity_type_name
        assert ws_entities.column_dimensions['B'].width == 25  # entity_type_count

    def test_empty_data_all_sheets(self, temp_dir: str) -> None:
        """Test that empty data creates headers-only sheets."""
        empty_data: ExtractionResult = {
            'block_counts': {},
            'block_entities': {},
            'block_layer_pairs': {},
            'block_rotation_counts': {},
            'layer_insertion_counts': {},
            'layer_entity_counts': {},
            'entity_type_counts': {},
            'block_trimming_data': {}
        }
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load all sheets and verify headers only
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_COUNTS)
        assert len(df_blocks) == 0
        assert list(df_blocks.columns) == [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
            EXCEL_COLUMN_BLOCK_LAYER_NAME,
            EXCEL_COLUMN_BLOCK_ROTATION_0,
            EXCEL_COLUMN_BLOCK_ROTATION_90,
            EXCEL_COLUMN_BLOCK_ROTATION_180,
            EXCEL_COLUMN_BLOCK_ROTATION_270,
            EXCEL_COLUMN_BLOCK_ROTATION_OTHER
        ]

        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert len(df_layers) == 0

        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert len(df_entities) == 0

    def test_rotation_counts_sum_to_total(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that rotation columns sum to block_insertion_count for each row."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Counts sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_COUNTS)

        # Verify sum of rotation counts equals insertion count for each row
        for _, row in df.iterrows():
            rotation_sum = (
                row[EXCEL_COLUMN_BLOCK_ROTATION_0] +
                row[EXCEL_COLUMN_BLOCK_ROTATION_90] +
                row[EXCEL_COLUMN_BLOCK_ROTATION_180] +
                row[EXCEL_COLUMN_BLOCK_ROTATION_270] +
                row[EXCEL_COLUMN_BLOCK_ROTATION_OTHER]
            )
            assert rotation_sum == row[EXCEL_COLUMN_BLOCK_INSERTION_COUNT]

    def test_rotation_counts_are_integers(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that all rotation counts are non-negative integers."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Counts sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_COUNTS)

        # Verify all rotation counts are non-negative integers
        for col in [EXCEL_COLUMN_BLOCK_ROTATION_0, EXCEL_COLUMN_BLOCK_ROTATION_90,
                    EXCEL_COLUMN_BLOCK_ROTATION_180, EXCEL_COLUMN_BLOCK_ROTATION_270,
                    EXCEL_COLUMN_BLOCK_ROTATION_OTHER]:
            for value in df[col]:
                assert isinstance(value, (int, float))  # pandas may use int64 or float64
                assert value >= 0
                assert value == int(value)  # No fractional parts

    def test_filename_format_unchanged(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that timestamped filename format is maintained."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify filename pattern: test_drawing_blocks_YYYYMMDD_HHMMSS.xlsx
        filename = Path(excel_path).name
        pattern = r'test_drawing_blocks_\d{8}_\d{6}\.xlsx'
        assert re.match(pattern, filename), f"Filename '{filename}' doesn't match pattern"

        # Verify file exists at the returned path
        assert Path(excel_path).exists()

    def test_none_data_raises_error(self, temp_dir: str) -> None:
        """Test that None data raises ValueError."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')

        with pytest.raises(ValueError, match="extraction_data cannot be None"):
            write_excel(None, output_path)  # type: ignore[arg-type]

    def test_block_trimming_analysis_sheet_exists(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet exists."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS in wb.sheetnames

    def test_block_trimming_analysis_sheet_headers(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Trimming Analysis sheet has correct column headers."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)

        # Verify all expected columns are present
        expected_columns = [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
            EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
            EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
            EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS
        ]

        for col in expected_columns:
            assert col in df.columns

        # Verify exactly 5 columns
        assert len(df.columns) == 5

    def test_block_trimming_analysis_data_types(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Trimming Analysis sheet has correct data types."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)

        # Width and height should be numeric
        for value in df[EXCEL_COLUMN_BLOCK_NATIVE_WIDTH]:
            assert isinstance(value, (int, float))
            assert value >= 0

        for value in df[EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT]:
            assert isinstance(value, (int, float))
            assert value >= 0

        # Segments should be strings (comma-separated values)
        for value in df[EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS]:
            assert isinstance(value, str) or pd.isna(value)

        for value in df[EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS]:
            assert isinstance(value, str) or pd.isna(value)

    def test_block_trimming_analysis_segment_formatting(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that segments are formatted as comma-separated strings."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)

        # Find VALVE row (has multi-segment data)
        valve_row = df[df[EXCEL_COLUMN_BLOCK_NAME] == 'VALVE'].iloc[0]

        # Verify segments are comma-separated strings
        vertical_segments = valve_row[EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS]
        assert isinstance(vertical_segments, str)
        assert ',' in vertical_segments
        assert '10.0, 80.0, 10.0' == vertical_segments

        horizontal_segments = valve_row[EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS]
        assert isinstance(horizontal_segments, str)
        assert ',' in horizontal_segments
        assert '5.0, 40.0, 5.0' == horizontal_segments

    def test_block_trimming_analysis_sorting(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet is sorted alphabetically by block name."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)

        # Verify blocks are sorted alphabetically
        block_names = df[EXCEL_COLUMN_BLOCK_NAME].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_empty_data(self, temp_dir: str) -> None:
        """Test that empty block_trimming_data creates sheet with headers only."""
        empty_data: ExtractionResult = {
            'block_counts': {},
            'block_entities': {},
            'block_layer_pairs': {},
            'block_rotation_counts': {},
            'layer_insertion_counts': {},
            'layer_entity_counts': {},
            'entity_type_counts': {},
            'block_trimming_data': {}
        }

        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 5

    def test_block_trimming_analysis_auto_filter(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet has auto-filter applied."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_TRIMMING_ANALYSIS]

        # Verify auto-filter is applied
        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref != ''
