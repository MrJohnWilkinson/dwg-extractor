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
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_LAYER_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
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
            'block_scale_data': {
                ('VALVE', 'Layer1'): (1.0, 1.0),
                ('VALVE', 'Layer2'): (-1.0, 1.0),
                ('PIPE', 'Layer1'): (1.0, -1.0),
                ('TAG', 'Layer1'): (-1.0, -1.0)
            },
            'layer_block_insertion_counts': {'Layer1': 15, 'Layer2': 3},
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
        assert EXCEL_SHEET_BLOCK_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames
        assert len(wb.sheetnames) == 4

    def test_block_analysis_sheet_simplified(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Analysis sheet has correct simplified structure (4 columns, no rotations)."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)

        # Verify headers - simplified to 4 columns only
        assert list(df.columns) == [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
            EXCEL_COLUMN_BLOCK_LAYER_NAME
        ]

        # Verify data rows (4 block-layer pairs)
        assert len(df) == 4
        # First row should be VALVE on Layer1 with 7 insertions (sorted by count descending)
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
            EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
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

        # Block Analysis: sorted by block_insertion_count descending
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
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

        # Verify auto-filter on Block Analysis sheet
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.auto_filter.ref is not None

        # Verify auto-filter on Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.auto_filter.ref is not None

        # Verify auto-filter on Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.auto_filter.ref is not None

        # Verify auto-filter on Block Geometry Analysis sheet
        ws_geometry = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]
        assert ws_geometry.auto_filter.ref is not None

    def test_all_sheets_column_widths(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that column widths are set correctly on all sheets."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Block Analysis sheet (simplified - 4 columns only)
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.column_dimensions['A'].width == 30  # block_name
        assert ws_blocks.column_dimensions['B'].width == 25  # block_insertion_count
        assert ws_blocks.column_dimensions['C'].width == 25  # block_entity_count
        assert ws_blocks.column_dimensions['D'].width == 25  # block_layer_name

        # Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.column_dimensions['A'].width == 30  # layer_name
        assert ws_layers.column_dimensions['B'].width == 25  # layer_block_insertion_count
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
            'block_scale_data': {},
            'block_scale_data': {},
            'layer_block_insertion_counts': {},
            'layer_entity_counts': {},
            'entity_type_counts': {},
            'block_trimming_data': {}
        }
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load all sheets and verify headers only
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
        assert len(df_blocks) == 0
        assert list(df_blocks.columns) == [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
            EXCEL_COLUMN_BLOCK_LAYER_NAME
        ]

        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert len(df_layers) == 0

        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert len(df_entities) == 0

    def test_block_geometry_analysis_has_rotations(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Geometry Analysis sheet contains rotation columns."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Geometry Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify rotation columns exist
        assert EXCEL_COLUMN_BLOCK_ROTATION_0 in df.columns
        assert EXCEL_COLUMN_BLOCK_ROTATION_90 in df.columns
        assert EXCEL_COLUMN_BLOCK_ROTATION_180 in df.columns
        assert EXCEL_COLUMN_BLOCK_ROTATION_270 in df.columns
        assert EXCEL_COLUMN_BLOCK_ROTATION_OTHER in df.columns

    def test_block_geometry_analysis_has_scales(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Geometry Analysis sheet contains scale columns."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Geometry Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify scale columns exist
        assert EXCEL_COLUMN_BLOCK_SCALE_X in df.columns
        assert EXCEL_COLUMN_BLOCK_SCALE_Y in df.columns

        # Verify scale data is present
        for value in df[EXCEL_COLUMN_BLOCK_SCALE_X]:
            assert isinstance(value, (int, float))
        for value in df[EXCEL_COLUMN_BLOCK_SCALE_Y]:
            assert isinstance(value, (int, float))

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
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames

    def test_block_geometry_analysis_sheet_consolidated(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Geometry Analysis sheet has all 13 columns consolidated."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify all expected columns are present in correct order
        expected_columns = [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_LAYER_NAME,
            EXCEL_COLUMN_BLOCK_ROTATION_0,
            EXCEL_COLUMN_BLOCK_ROTATION_90,
            EXCEL_COLUMN_BLOCK_ROTATION_180,
            EXCEL_COLUMN_BLOCK_ROTATION_270,
            EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
            EXCEL_COLUMN_BLOCK_SCALE_X,
            EXCEL_COLUMN_BLOCK_SCALE_Y,
            EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
            EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
            EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
            EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS
        ]

        assert list(df.columns) == expected_columns

        # Verify exactly 13 columns
        assert len(df.columns) == 13

        # Verify sort by block_name alphabetical
        block_names = df[EXCEL_COLUMN_BLOCK_NAME].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_data_types(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test Block Trimming Analysis sheet has correct data types."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

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

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Find first VALVE row (has multi-segment data) - there will be multiple rows for VALVE
        valve_row = df[df[EXCEL_COLUMN_BLOCK_NAME] == 'VALVE'].iloc[0]

        # Verify segments are comma-separated strings
        vertical_segments = valve_row[EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS]
        assert isinstance(vertical_segments, str)
        assert ',' in vertical_segments
        assert '10, 80, 10' == vertical_segments

        horizontal_segments = valve_row[EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS]
        assert isinstance(horizontal_segments, str)
        assert ',' in horizontal_segments
        assert '5, 40, 5' == horizontal_segments

    def test_block_trimming_analysis_sorting(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet is sorted alphabetically by block name."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify blocks are sorted alphabetically
        block_names = df[EXCEL_COLUMN_BLOCK_NAME].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_empty_data(self, temp_dir: str) -> None:
        """Test that empty block_layer_pairs creates sheet with headers only."""
        empty_data: ExtractionResult = {
            'block_counts': {},
            'block_entities': {},
            'block_layer_pairs': {},
            'block_rotation_counts': {},
            'block_scale_data': {},
            'layer_block_insertion_counts': {},
            'layer_entity_counts': {},
            'entity_type_counts': {},
            'block_trimming_data': {}
        }

        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 13

    def test_block_trimming_analysis_auto_filter(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet has auto-filter applied."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Verify auto-filter is applied
        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref != ''

    def test_block_geometry_analysis_sorted_alphabetically(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Geometry Analysis sheet is sorted alphabetically by block name."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify blocks are sorted alphabetically
        block_names = df[EXCEL_COLUMN_BLOCK_NAME].tolist()
        assert block_names == sorted(block_names), "Block Geometry Analysis should be sorted alphabetically by block_name"

    def test_block_trimming_analysis_block_layer_pairs(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Trimming Analysis sheet contains block-layer pairs with geometry data."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify number of rows matches block-layer pairs (4 pairs in sample data)
        assert len(df) == 4

        # Verify VALVE appears on two layers with identical geometry
        valve_rows = df[df[EXCEL_COLUMN_BLOCK_NAME] == 'VALVE']
        assert len(valve_rows) == 2

        # Verify both VALVE rows have identical geometry data
        valve_layer1 = valve_rows[valve_rows[EXCEL_COLUMN_BLOCK_LAYER_NAME] == 'Layer1'].iloc[0]
        valve_layer2 = valve_rows[valve_rows[EXCEL_COLUMN_BLOCK_LAYER_NAME] == 'Layer2'].iloc[0]

        assert valve_layer1[EXCEL_COLUMN_BLOCK_NATIVE_WIDTH] == valve_layer2[EXCEL_COLUMN_BLOCK_NATIVE_WIDTH]
        assert valve_layer1[EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT] == valve_layer2[EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT]
        assert valve_layer1[EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS] == valve_layer2[EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS]
        assert valve_layer1[EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS] == valve_layer2[EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS]

        # Verify geometry data is correct
        assert valve_layer1[EXCEL_COLUMN_BLOCK_NATIVE_WIDTH] == 100.0
        assert valve_layer1[EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT] == 50.0

    def test_geometry_sheet_red_highlighting(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that mirrored blocks (negative scales) have red fill highlighting."""
        from openpyxl.styles import PatternFill

        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Check rows for red highlighting based on sample data
        # VALVE/Layer2 has (-1.0, 1.0) - should be red (row 3 or 4 depending on sort)
        # PIPE/Layer1 has (1.0, -1.0) - should be red
        # TAG/Layer1 has (-1.0, -1.0) - should be red
        # VALVE/Layer1 has (1.0, 1.0) - should NOT be red

        red_rows = 0
        non_red_rows = 0

        # Iterate through data rows (skip header at row 1)
        for row_idx in range(2, ws.max_row + 1):
            x_scale = ws.cell(row=row_idx, column=8).value  # Column H
            y_scale = ws.cell(row=row_idx, column=9).value  # Column I
            cell_fill = ws.cell(row=row_idx, column=1).fill  # Check first column fill

            if (isinstance(x_scale, (int, float)) and x_scale < 0) or (isinstance(y_scale, (int, float)) and y_scale < 0):
                # Should have red fill
                assert cell_fill.start_color.rgb == 'FFFF0000', f"Row {row_idx} with scales ({x_scale}, {y_scale}) should have red fill"
                red_rows += 1
            else:
                # Should NOT have red fill (no fill or different color)
                assert cell_fill.start_color.rgb != 'FFFF0000', f"Row {row_idx} with scales ({x_scale}, {y_scale}) should NOT have red fill"
                non_red_rows += 1

        # Verify we have both red and non-red rows
        assert red_rows == 3, f"Expected 3 mirrored blocks, got {red_rows}"
        assert non_red_rows == 1, f"Expected 1 non-mirrored block, got {non_red_rows}"

    def test_block_geometry_analysis_column_widths(self, temp_dir: str, sample_extraction_data: ExtractionResult) -> None:
        """Test that Block Geometry Analysis sheet has appropriate column widths for 13 columns."""
        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Verify column widths for 13-column layout
        assert ws.column_dimensions['A'].width == 30  # block_name
        assert ws.column_dimensions['B'].width == 25  # block_layer_name
        assert ws.column_dimensions['C'].width == 12  # block_rotation_0
        assert ws.column_dimensions['D'].width == 12  # block_rotation_90
        assert ws.column_dimensions['E'].width == 12  # block_rotation_180
        assert ws.column_dimensions['F'].width == 12  # block_rotation_270
        assert ws.column_dimensions['G'].width == 12  # block_rotation_other
        assert ws.column_dimensions['H'].width == 15  # block_scale_x
        assert ws.column_dimensions['I'].width == 15  # block_scale_y
        assert ws.column_dimensions['J'].width == 20  # block_native_width
        assert ws.column_dimensions['K'].width == 20  # block_native_height
        assert ws.column_dimensions['L'].width == 40  # block_vertical_segments
        assert ws.column_dimensions['M'].width == 40  # block_horizontal_segments

    def test_block_geometry_analysis_empty_data(self, temp_dir: str) -> None:
        """Test that empty block_layer_pairs creates sheet with all 13 column headers."""
        empty_data: ExtractionResult = {
            'block_counts': {},
            'block_entities': {},
            'block_layer_pairs': {},
            'block_rotation_counts': {},
            'block_scale_data': {},
            'layer_block_insertion_counts': {},
            'layer_entity_counts': {},
            'entity_type_counts': {},
            'block_trimming_data': {}
        }

        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0

        # Verify all 13 column headers
        expected_columns = [
            EXCEL_COLUMN_BLOCK_NAME,
            EXCEL_COLUMN_BLOCK_LAYER_NAME,
            EXCEL_COLUMN_BLOCK_ROTATION_0,
            EXCEL_COLUMN_BLOCK_ROTATION_90,
            EXCEL_COLUMN_BLOCK_ROTATION_180,
            EXCEL_COLUMN_BLOCK_ROTATION_270,
            EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
            EXCEL_COLUMN_BLOCK_SCALE_X,
            EXCEL_COLUMN_BLOCK_SCALE_Y,
            EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
            EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
            EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
            EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS
        ]
        assert list(df.columns) == expected_columns

    def test_block_trimming_analysis_missing_geometry(self, temp_dir: str) -> None:
        """Test that blocks in block_layer_pairs but not in block_trimming_data are skipped gracefully."""
        # Data with a block-layer pair that has no geometry data
        data_with_missing_geometry: ExtractionResult = {
            'block_counts': {'VALVE': 10, 'ANONYMOUS': 5},
            'block_entities': {'VALVE': 8, 'ANONYMOUS': 0},
            'block_layer_pairs': {
                ('VALVE', 'Layer1'): 10,
                ('ANONYMOUS', 'Layer1'): 5  # This block has no geometry data
            },
            'block_rotation_counts': {},
            'block_scale_data': {},
            'layer_block_insertion_counts': {'Layer1': 15},
            'layer_entity_counts': {'Layer1': 25},
            'entity_type_counts': {'INSERT': 15},
            'block_trimming_data': {
                'VALVE': {
                    'native_width': 100.0,
                    'native_height': 50.0,
                    'vertical_segments': [10.0, 80.0, 10.0],
                    'horizontal_segments': [5.0, 40.0, 5.0]
                }
                # ANONYMOUS block intentionally missing from block_trimming_data
            }
        }

        output_path = os.path.join(temp_dir, 'test_drawing.dwg')
        excel_path = write_excel(data_with_missing_geometry, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should only have VALVE row, ANONYMOUS should be skipped
        assert len(df) == 1
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_NAME] == 'VALVE'
        assert df.iloc[0][EXCEL_COLUMN_BLOCK_LAYER_NAME] == 'Layer1'
