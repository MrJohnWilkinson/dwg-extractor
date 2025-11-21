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

import os
import re
import tempfile
from pathlib import Path
from typing import Iterator

import pandas as pd
import pytest
from openpyxl import load_workbook

from core.constants import (
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_XDATA_APPS,
    EXCEL_COLUMN_ENTITY_TYPE_COUNT,
    EXCEL_COLUMN_ENTITY_TYPE_NAME,
    EXCEL_COLUMN_LAYER_ANNOTATION_COUNT,
    EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_LAYER_ENTITY_COUNT,
    EXCEL_COLUMN_LAYER_NAME,
    EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
    EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from core.excel_formatting import format_header
from core.excel_writer import write_excel
from core.extractor import ExtractionResult


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
            "block_counts": {"VALVE": 10, "PIPE": 5, "TAG": 3},
            "block_entities": {"VALVE": 8, "PIPE": 12, "TAG": 4},
            "block_layer_pairs": {
                ("VALVE", "Layer1"): 7,
                ("VALVE", "Layer2"): 3,
                ("PIPE", "Layer1"): 5,
                ("TAG", "Layer1"): 3,
            },
            "block_rotation_counts": {
                ("VALVE", "Layer1", "0"): 5,
                ("VALVE", "Layer1", "90"): 2,
                ("VALVE", "Layer2", "0"): 3,
                ("PIPE", "Layer1", "0"): 3,
                ("PIPE", "Layer1", "180"): 2,
                ("TAG", "Layer1", "other"): 3,
            },
            "block_scale_data": {
                "VALVE": {(1.0, 1.0), (-1.0, 1.0)},
                "PIPE": {(1.0, -1.0)},
                "TAG": {(-1.0, -1.0)},
            },
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"Layer1": 15, "Layer2": 3},
            "layer_entity_counts": {"Layer1": 25, "Layer2": 10},
            "layer_unique_color_counts": {"Layer1": 3, "Layer2": 1},
            "layer_annotation_counts": {"Layer1": 5, "Layer2": 2},
            "annotation_data": {},
            "entity_type_counts": {"INSERT": 18, "LINE": 15, "CIRCLE": 8},
            "color_analysis_data": [],
            "block_trimming_data": {
                "VALVE": {
                    "native_width": 100.0,
                    "native_height": 50.0,
                    "vertical_segments": [10.0, 80.0, 10.0],
                    "horizontal_segments": [5.0, 40.0, 5.0],
                },
                "PIPE": {
                    "native_width": 200.0,
                    "native_height": 100.0,
                    "vertical_segments": [20.0, 160.0, 20.0],
                    "horizontal_segments": [10.0, 80.0, 10.0],
                },
                "TAG": {
                    "native_width": 50.0,
                    "native_height": 25.0,
                    "vertical_segments": [50.0],
                    "horizontal_segments": [25.0],
                },
            },
        }

    def test_write_excel_four_sheets(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that six sheets are created with correct names."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load and verify sheet names
        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_BLOCK_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ANNOTATIONS_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_COLOR_ANALYSIS in wb.sheetnames
        assert len(wb.sheetnames) == 6

    def test_block_analysis_sheet_simplified(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Analysis sheet has correct simplified structure (5 columns, no rotations)."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)

        # Verify headers - simplified to 5 columns only (formatted)
        assert list(df.columns) == [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_XDATA_APPS),
        ]

        # Verify data rows (4 block-layer pairs)
        assert len(df) == 4
        # First row should be VALVE on Layer1 with 7 insertions (sorted by count descending)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VALVE"
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT)] == 7
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT)] == 8
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME)] == "Layer1"

    def test_layer_analysis_sheet_structure(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Layer Analysis sheet has correct columns and data."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Layer Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)

        # Verify headers (formatted) - now includes color count and text/mtext count columns
        assert list(df.columns) == [
            format_header(EXCEL_COLUMN_LAYER_NAME),
            format_header(EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT),
            format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT),
            format_header(EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT),
            format_header(EXCEL_COLUMN_LAYER_ANNOTATION_COUNT),
        ]

        # Verify data rows
        assert len(df) == 2
        # Sorted by layer_entity_count descending
        assert df.iloc[0][format_header(EXCEL_COLUMN_LAYER_NAME)] == "Layer1"
        assert df.iloc[0][format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT)] == 25
        assert df.iloc[0][format_header(EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT)] == 3

    def test_entity_summary_sheet_structure(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Entity Summary sheet has correct columns and data."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Entity Summary sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)

        # Verify headers (formatted)
        assert list(df.columns) == [
            format_header(EXCEL_COLUMN_ENTITY_TYPE_NAME),
            format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT),
        ]

        # Verify data rows
        assert len(df) == 3

    def test_all_sheets_sorted(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that all sheets are sorted correctly."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Block Analysis: sorted by block_insertion_count descending
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
        # First row should be VALVE/Layer1 with 7
        assert df_blocks.iloc[0][format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT)] == 7
        # Second row should be PIPE/Layer1 with 5
        assert df_blocks.iloc[1][format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT)] == 5
        # Third and fourth rows should both have 3
        assert df_blocks.iloc[2][format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT)] == 3

        # Layer Analysis: sorted by layer_entity_count descending
        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert (
            df_layers.iloc[0][format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT)] == 25
        )  # Layer1
        assert (
            df_layers.iloc[1][format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT)] == 10
        )  # Layer2

        # Entity Summary: sorted by entity_type_count descending
        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert (
            df_entities.iloc[0][format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT)] == 18
        )  # INSERT
        assert (
            df_entities.iloc[1][format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT)] == 15
        )  # LINE
        assert (
            df_entities.iloc[2][format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT)] == 8
        )  # CIRCLE

    def test_all_sheets_autofilter(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that auto-filters are applied to all sheets."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
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

    def test_all_sheets_column_widths(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that column widths are set correctly on all sheets."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Block Analysis sheet (simplified - 5 columns)
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.column_dimensions["A"].width == 30  # block_name
        assert ws_blocks.column_dimensions["B"].width == 25  # block_insertion_count
        assert ws_blocks.column_dimensions["C"].width == 25  # block_entity_count
        assert ws_blocks.column_dimensions["D"].width == 25  # block_layer_name
        assert ws_blocks.column_dimensions["E"].width == 30  # block_xdata_apps

        # Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.column_dimensions["A"].width == 30  # layer_name
        assert (
            ws_layers.column_dimensions["B"].width == 25
        )  # layer_block_insertion_count
        assert ws_layers.column_dimensions["C"].width == 25  # layer_entity_count

        # Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.column_dimensions["A"].width == 25  # entity_type_name
        assert ws_entities.column_dimensions["B"].width == 25  # entity_type_count

    def test_empty_data_all_sheets(self, temp_dir: str) -> None:
        """Test that empty data creates headers-only sheets."""
        empty_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {},
        }
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(empty_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load all sheets and verify headers only
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
        assert len(df_blocks) == 0
        assert list(df_blocks.columns) == [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_XDATA_APPS),
        ]

        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert len(df_layers) == 0

        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert len(df_entities) == 0

    def test_block_geometry_analysis_has_rotations(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Geometry Analysis sheet contains rotation columns."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Geometry Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify rotation columns exist (formatted)
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_0) in df.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_90) in df.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_180) in df.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_270) in df.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER) in df.columns

    def test_block_geometry_analysis_has_scales(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Geometry Analysis sheet contains scale columns."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load Block Geometry Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify scale columns exist (formatted)
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_X) in df.columns
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_Y) in df.columns

        # Verify scale data is present (can be numeric or "VARIES" string)
        for value in df[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)]:
            assert isinstance(value, (int, float, str))
        for value in df[format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)]:
            assert isinstance(value, (int, float, str))

    def test_filename_format_unchanged(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that timestamped filename format is maintained."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify filename pattern: test_drawing_blocks_YYYYMMDD_HHMMSS.xlsx
        filename = Path(excel_path).name
        pattern = r"test_drawing_blocks_\d{8}_\d{6}\.xlsx"
        assert re.match(pattern, filename), (
            f"Filename '{filename}' doesn't match pattern"
        )

        # Verify file exists at the returned path
        assert Path(excel_path).exists()

    def test_none_data_raises_error(self, temp_dir: str) -> None:
        """Test that None data raises ValueError."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")

        with pytest.raises(ValueError, match="extraction_data cannot be None"):
            write_excel(None, output_path)  # type: ignore[arg-type]

    def test_block_trimming_analysis_sheet_exists(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet exists."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames

    def test_block_geometry_analysis_sheet_consolidated(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Geometry Analysis sheet has all 13 columns consolidated."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify all expected columns are present in correct order (formatted)
        expected_columns = [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_0),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_90),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_180),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_270),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_X),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_Y),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS),
            format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS),
        ]

        assert list(df.columns) == expected_columns

        # Verify exactly 13 columns
        assert len(df.columns) == 13

        # Verify sort by block_name alphabetical
        block_names = df[format_header(EXCEL_COLUMN_BLOCK_NAME)].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_data_types(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Trimming Analysis sheet has correct data types."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Width and height should be numeric (formatted column names)
        for value in df[format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH)]:
            assert isinstance(value, (int, float))
            assert value >= 0

        for value in df[format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT)]:
            assert isinstance(value, (int, float))
            assert value >= 0

        # Segments should be strings (comma-separated values)
        for value in df[format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS)]:
            assert isinstance(value, str) or pd.isna(value)

        for value in df[format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS)]:
            assert isinstance(value, str) or pd.isna(value)

    def test_block_trimming_analysis_segment_formatting(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that segments are formatted as comma-separated strings."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Find first VALVE row (has multi-segment data) - there will be multiple rows for VALVE (formatted column names)
        valve_row = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VALVE"].iloc[0]

        # Verify segments are comma-separated strings
        vertical_segments = valve_row[
            format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS)
        ]
        assert isinstance(vertical_segments, str)
        assert "," in vertical_segments
        assert "10, 80, 10" == vertical_segments

        horizontal_segments = valve_row[
            format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS)
        ]
        assert isinstance(horizontal_segments, str)
        assert "," in horizontal_segments
        assert "5, 40, 5" == horizontal_segments

    def test_block_trimming_analysis_sorting(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet is sorted alphabetically by block name."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify blocks are sorted alphabetically (formatted column names)
        block_names = df[format_header(EXCEL_COLUMN_BLOCK_NAME)].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_empty_data(self, temp_dir: str) -> None:
        """Test that empty block_layer_pairs creates sheet with headers only."""
        empty_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 13

    def test_block_trimming_analysis_auto_filter(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet has auto-filter applied."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Verify auto-filter is applied
        assert ws.auto_filter.ref is not None
        assert ws.auto_filter.ref != ""

    def test_block_geometry_analysis_sorted_alphabetically(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Geometry Analysis sheet is sorted alphabetically by block name."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify blocks are sorted alphabetically (formatted column names)
        block_names = df[format_header(EXCEL_COLUMN_BLOCK_NAME)].tolist()
        assert block_names == sorted(block_names), (
            "Block Geometry Analysis should be sorted alphabetically by block_name"
        )

    def test_block_trimming_analysis_block_layer_pairs(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet contains block-layer pairs with geometry data."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Verify number of rows matches block-layer pairs (4 pairs in sample data)
        assert len(df) == 4

        # Verify VALVE appears on two layers with identical geometry
        valve_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VALVE"]
        assert len(valve_rows) == 2

        # Verify both VALVE rows have identical geometry data
        valve_layer1 = valve_rows[
            valve_rows[format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME)] == "Layer1"
        ].iloc[0]
        valve_layer2 = valve_rows[
            valve_rows[format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME)] == "Layer2"
        ].iloc[0]

        assert (
            valve_layer1[format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH)]
            == valve_layer2[format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH)]
        )
        assert (
            valve_layer1[format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT)]
            == valve_layer2[format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT)]
        )
        assert (
            valve_layer1[format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS)]
            == valve_layer2[format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS)]
        )
        assert (
            valve_layer1[format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS)]
            == valve_layer2[format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS)]
        )

        # Verify geometry data is correct
        assert valve_layer1[format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH)] == 100.0
        assert valve_layer1[format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT)] == 50.0

    def test_geometry_sheet_variance_highlighting(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that blocks with scale variance have yellow fill highlighting."""

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Check rows for highlighting based on sample data with negative scales
        # VALVE has variance: {(1.0, 1.0), (-1.0, 1.0)} - X varies with negatives - should show "VARIES (-)" with red
        # PIPE has no variance: {(1.0, -1.0)} - should show numeric -1.0 with orange
        # TAG has no variance: {(-1.0, -1.0)} - should show numeric -1.0 with orange

        from core.constants import (
            EXCEL_FILL_COLOR_SCALE_NEGATIVE,
            EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        )

        red_rows = 0
        orange_rows = 0

        # Iterate through data rows (skip header at row 1)
        for row_idx in range(2, ws.max_row + 1):
            x_scale = ws.cell(row=row_idx, column=8).value  # Column H
            y_scale = ws.cell(row=row_idx, column=9).value  # Column I
            cell_fill = ws.cell(row=row_idx, column=1).fill  # Check first column fill

            if x_scale == "VARIES (-)" or y_scale == "VARIES (-)":
                # Should have red fill
                assert (
                    cell_fill.start_color.rgb
                    == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
                ), (
                    f"Row {row_idx} with scales ({x_scale}, {y_scale}) should have red fill for 'VARIES (-)'"
                )
                red_rows += 1
            elif (isinstance(x_scale, (int, float)) and x_scale < 0) or (
                isinstance(y_scale, (int, float)) and y_scale < 0
            ):
                # Should have orange fill for negative numbers
                assert cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE, (
                    f"Row {row_idx} with scales ({x_scale}, {y_scale}) should have orange fill for negative number"
                )
                orange_rows += 1

        # Verify we have the expected highlighting
        # VALVE appears on 2 layers with variance including negatives - both rows should be red
        assert red_rows == 2, (
            f"Expected 2 rows with 'VARIES (-)' (VALVE on both layers), got {red_rows}"
        )
        # PIPE and TAG have consistent negative scales - both should be orange
        assert orange_rows == 2, (
            f"Expected 2 rows with negative numbers (PIPE, TAG), got {orange_rows}"
        )

    def test_block_geometry_analysis_column_widths(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Geometry Analysis sheet has appropriate column widths for 13 columns."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Verify column widths for 13-column layout
        assert ws.column_dimensions["A"].width == 30  # block_name
        assert ws.column_dimensions["B"].width == 25  # block_layer_name
        assert ws.column_dimensions["C"].width == 12  # block_rotation_0
        assert ws.column_dimensions["D"].width == 12  # block_rotation_90
        assert ws.column_dimensions["E"].width == 12  # block_rotation_180
        assert ws.column_dimensions["F"].width == 12  # block_rotation_270
        assert ws.column_dimensions["G"].width == 12  # block_rotation_other
        assert ws.column_dimensions["H"].width == 15  # block_scale_x
        assert ws.column_dimensions["I"].width == 15  # block_scale_y
        assert ws.column_dimensions["J"].width == 20  # block_native_width
        assert ws.column_dimensions["K"].width == 20  # block_native_height
        assert ws.column_dimensions["L"].width == 40  # block_vertical_segments
        assert ws.column_dimensions["M"].width == 40  # block_horizontal_segments

    def test_block_geometry_analysis_empty_data(self, temp_dir: str) -> None:
        """Test that empty block_layer_pairs creates sheet with all 13 column headers."""
        empty_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0

        # Verify all 13 column headers (formatted)
        expected_columns = [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_0),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_90),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_180),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_270),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_X),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_Y),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS),
            format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS),
        ]
        assert list(df.columns) == expected_columns

    def test_block_trimming_analysis_missing_geometry(self, temp_dir: str) -> None:
        """Test that blocks in block_layer_pairs but not in block_trimming_data are skipped gracefully."""
        # Data with a block-layer pair that has no geometry data
        data_with_missing_geometry: ExtractionResult = {
            "block_counts": {"VALVE": 10, "ANONYMOUS": 5},
            "block_entities": {"VALVE": 8, "ANONYMOUS": 0},
            "block_layer_pairs": {
                ("VALVE", "Layer1"): 10,
                ("ANONYMOUS", "Layer1"): 5,  # This block has no geometry data
            },
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"Layer1": 15},
            "layer_entity_counts": {"Layer1": 25},
            "layer_unique_color_counts": {"Layer1": 0},
            "layer_annotation_counts": {"Layer1": 0},
            "annotation_data": {},
            "entity_type_counts": {"INSERT": 15},
            "color_analysis_data": [],
            "block_trimming_data": {
                "VALVE": {
                    "native_width": 100.0,
                    "native_height": 50.0,
                    "vertical_segments": [10.0, 80.0, 10.0],
                    "horizontal_segments": [5.0, 40.0, 5.0],
                }
                # ANONYMOUS block intentionally missing from block_trimming_data
            },
        }

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(data_with_missing_geometry, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should only have VALVE row, ANONYMOUS should be skipped
        assert len(df) == 1
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VALVE"
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME)] == "Layer1"

    def test_write_excel_value_error_invalid_data(self, temp_dir: str) -> None:
        """Test that write_excel raises exception for invalid extraction data structure."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")

        # Test with missing required keys
        invalid_data_missing_keys: dict[str, dict[str, int]] = {
            "block_counts": {"VALVE": 10}
            # Missing other required keys
        }

        # The function should raise an exception when required keys are missing
        # KeyError is raised initially, but may be wrapped in IndexError during cleanup
        with pytest.raises((ValueError, KeyError, IndexError, Exception)):
            write_excel(invalid_data_missing_keys, output_path)  # type: ignore[arg-type]

    def test_write_excel_generic_exception_save_failure(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that generic exceptions during Excel save are properly handled."""

        # Use an invalid output path to trigger save failure
        invalid_path = os.path.join(temp_dir, "nonexistent_dir", "test.dwg")

        # Verify exception is raised for invalid path
        with pytest.raises(Exception):
            write_excel(sample_extraction_data, invalid_path)

    def test_constants_match_dataframe_columns(self, temp_dir: str) -> None:
        """Test that constants.py values exactly match DataFrame column names in all sheets."""
        from core.extractor import extract_blocks

        # Extract real data from sample file
        extraction_data = extract_blocks("app/tests/assets/sample_drawing.dxf")

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(extraction_data, output_path)

        # Load all sheets and verify column names match formatted constants

        # Block Analysis sheet - 5 columns
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
        assert list(df_blocks.columns) == [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_XDATA_APPS),
        ]

        # Layer Analysis sheet - 5 columns (now includes color count and text/mtext count)
        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        assert list(df_layers.columns) == [
            format_header(EXCEL_COLUMN_LAYER_NAME),
            format_header(EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT),
            format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT),
            format_header(EXCEL_COLUMN_LAYER_UNIQUE_COLOR_COUNT),
            format_header(EXCEL_COLUMN_LAYER_ANNOTATION_COUNT),
        ]

        # Entity Summary sheet - 2 columns
        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        assert list(df_entities.columns) == [
            format_header(EXCEL_COLUMN_ENTITY_TYPE_NAME),
            format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT),
        ]

        # Block Geometry Analysis sheet - 13 columns
        df_geometry = pd.read_excel(
            excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
        )
        assert list(df_geometry.columns) == [
            format_header(EXCEL_COLUMN_BLOCK_NAME),
            format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_0),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_90),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_180),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_270),
            format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_X),
            format_header(EXCEL_COLUMN_BLOCK_SCALE_Y),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_VERTICAL_SEGMENTS),
            format_header(EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS),
        ]

    def test_spec_010_consolidated_geometry_sheet(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test spec 010: Block Geometry Analysis sheet has consolidated 13 columns with scales and rotations."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        df_geometry = pd.read_excel(
            excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
        )
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)

        # Verify Block Geometry Analysis has exactly 13 columns
        assert len(df_geometry.columns) == 13

        # Verify scale columns present (formatted)
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_X) in df_geometry.columns
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_Y) in df_geometry.columns

        # Verify rotation columns present (5 rotation categories, formatted)
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_0) in df_geometry.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_90) in df_geometry.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_180) in df_geometry.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_270) in df_geometry.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_OTHER) in df_geometry.columns

        # Verify Block Analysis sheet has ONLY 5 columns (no rotations)
        assert len(df_blocks.columns) == 5
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_0) not in df_blocks.columns
        assert format_header(EXCEL_COLUMN_BLOCK_ROTATION_90) not in df_blocks.columns

        # Verify highlighting for blocks with scale variance or negative scales
        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        from core.constants import (
            EXCEL_FILL_COLOR_SCALE_NEGATIVE,
            EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
        )

        # Check for highlighted rows (sample data has red and orange highlighting)
        # VALVE: {(1.0, 1.0), (-1.0, 1.0)} - X varies with negatives → red
        # PIPE: {(1.0, -1.0)} - Consistent negative Y → orange
        # TAG: {(-1.0, -1.0)} - Consistent negative X and Y → orange
        has_red_highlight = False
        has_orange_highlight = False
        for row_idx in range(2, ws.max_row + 1):
            x_scale = ws.cell(row=row_idx, column=8).value
            y_scale = ws.cell(row=row_idx, column=9).value
            cell_fill = ws.cell(row=row_idx, column=1).fill

            if x_scale == "VARIES (-)" or y_scale == "VARIES (-)":
                if (
                    cell_fill.start_color.rgb
                    == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
                ):
                    has_red_highlight = True
            elif (isinstance(x_scale, (int, float)) and x_scale < 0) or (
                isinstance(y_scale, (int, float)) and y_scale < 0
            ):
                if cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE:
                    has_orange_highlight = True

        assert has_red_highlight, (
            "VALVE block with 'VARIES (-)' should have red highlighting"
        )
        assert has_orange_highlight, (
            "PIPE and TAG blocks with consistent negative scales should have orange highlighting"
        )

    def test_spec_012_naming_conventions(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test spec 012: Excel headers are formatted from snake_case constants to Title Case."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load all sheets
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)
        df_layers = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)
        df_entities = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ENTITY_SUMMARY)
        df_geometry = pd.read_excel(
            excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
        )

        # Verify Excel headers are Title Case formatted from constants
        # Pattern: Title Case with spaces (e.g., "Block Name", "Layer Entity Count", "Block Rotation 0")
        import re

        # Pattern allows Title Case words followed by optional spaces and numbers
        title_case_pattern = re.compile(r"^([A-Z][A-Za-z0-9]*\s?)+\d*$")

        # Collect all column names
        all_columns = (
            list(df_blocks.columns)
            + list(df_layers.columns)
            + list(df_entities.columns)
            + list(df_geometry.columns)
        )

        # Verify all Excel headers follow Title Case pattern
        for column in all_columns:
            assert title_case_pattern.match(column), (
                f"Column '{column}' does not follow Title Case pattern"
            )

        # Verify specific formatted headers are present
        # Block domain columns (formatted)
        block_columns = [col for col in all_columns if col.startswith("Block")]
        assert format_header(EXCEL_COLUMN_BLOCK_NAME) in block_columns
        assert format_header(EXCEL_COLUMN_BLOCK_INSERTION_COUNT) in block_columns
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_X) in block_columns
        assert format_header(EXCEL_COLUMN_BLOCK_SCALE_Y) in block_columns

        # Layer domain columns (formatted)
        layer_columns = [col for col in all_columns if col.startswith("Layer")]
        assert format_header(EXCEL_COLUMN_LAYER_NAME) in layer_columns
        assert format_header(EXCEL_COLUMN_LAYER_BLOCK_INSERTION_COUNT) in layer_columns
        assert format_header(EXCEL_COLUMN_LAYER_ENTITY_COUNT) in layer_columns

        # Entity type domain columns (formatted)
        entity_type_columns = [
            col for col in all_columns if col.startswith("Entity Type")
        ]
        assert format_header(EXCEL_COLUMN_ENTITY_TYPE_NAME) in entity_type_columns
        assert format_header(EXCEL_COLUMN_ENTITY_TYPE_COUNT) in entity_type_columns

    def test_scale_variance_detection_varies_x_only(self, temp_dir: str) -> None:
        """Test that X scale variance is detected and displayed as VARIES."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # X_VARIES block has varying X scales: (1.0, 1.0), (2.0, 1.0), (1.5, 1.0)
        x_varies_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "X_VARIES"]
        assert len(x_varies_rows) > 0

        # All rows for X_VARIES should show "VARIES" in X Scale column
        for _, row in x_varies_rows.iterrows():
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES"
            # Y scale should be consistent (1.0)
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == 1.0

    def test_scale_variance_detection_varies_y_only(self, temp_dir: str) -> None:
        """Test that Y scale variance is detected and displayed as VARIES."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Y_VARIES block has varying Y scales: (1.0, 1.0), (1.0, 2.0), (1.0, 0.5)
        y_varies_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "Y_VARIES"]
        assert len(y_varies_rows) > 0

        # All rows for Y_VARIES should show "VARIES" in Y Scale column
        for _, row in y_varies_rows.iterrows():
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == "VARIES"
            # X scale should be consistent (1.0)
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == 1.0

    def test_scale_variance_detection_varies_both(self, temp_dir: str) -> None:
        """Test that both X and Y scale variance is detected and displayed as VARIES (-)."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # BOTH_VARY block has varying X and Y scales: (1.0, 1.0), (2.0, 2.0), (-1.0, 1.5)
        # Both axes have variance, and X includes negative values
        both_vary_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "BOTH_VARY"]
        assert len(both_vary_rows) > 0

        # All rows for BOTH_VARY should show "VARIES (-)" in X (has negatives) and "VARIES" in Y (all positive)
        for _, row in both_vary_rows.iterrows():
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES (-)"
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == "VARIES"

    def test_scale_variance_display_numeric_when_consistent(
        self, temp_dir: str
    ) -> None:
        """Test that numeric values are displayed when scales are consistent."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # CONSISTENT block has only one scale across all insertions: (1.5, 1.5)
        consistent_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "CONSISTENT"]
        assert len(consistent_rows) > 0

        # All rows for CONSISTENT should show numeric values (1.5, 1.5)
        for _, row in consistent_rows.iterrows():
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == 1.5
            assert row[format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == 1.5

    def test_variance_yellow_highlighting_applied(self, temp_dir: str) -> None:
        """Test that yellow highlighting is applied to rows with VARIES."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Count rows with yellow highlighting
        yellow_rows = 0
        for row_idx in range(2, ws.max_row + 1):
            cell_fill = ws.cell(row=row_idx, column=1).fill
            if cell_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE:
                yellow_rows += 1

        # Should have yellow highlighting for X_VARIES, Y_VARIES, and BOTH_VARY rows
        # Each appears on 2-3 layers, but we expect at least 3 rows highlighted
        assert yellow_rows >= 3, (
            f"Expected at least 3 rows with yellow highlighting, got {yellow_rows}"
        )

    def test_no_variance_no_highlighting(self, temp_dir: str) -> None:
        """Test that rows without VARIES have no yellow highlighting."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/scale_variance_test.dxf")
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(result, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Iterate through worksheet and verify CONSISTENT rows have no yellow fill
        for row_idx in range(2, ws.max_row + 1):
            block_name = ws.cell(row=row_idx, column=1).value
            if block_name == "CONSISTENT":
                cell_fill = ws.cell(row=row_idx, column=1).fill
                assert (
                    cell_fill.start_color.rgb
                    != EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE
                ), (
                    f"CONSISTENT block at row {row_idx} should NOT have yellow highlighting"
                )

    def test_write_excel_with_xdata_apps(self) -> None:
        """Test Excel generation includes XDATA Apps column in Block Analysis sheet."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock ExtractionResult with XDATA apps
            result: ExtractionResult = {
                "block_counts": {"BLOCK_A": 3, "BLOCK_B": 2},
                "block_entities": {"BLOCK_A": 5, "BLOCK_B": 3},
                "block_layer_pairs": {
                    ("BLOCK_A", "LAYER_1"): 3,
                    ("BLOCK_B", "LAYER_1"): 2,
                },
                "block_rotation_counts": {
                    ("BLOCK_A", "LAYER_1", "0"): 3,
                    ("BLOCK_B", "LAYER_1", "0"): 2,
                },
                "block_scale_data": {"BLOCK_A": {(1.0, 1.0)}, "BLOCK_B": {(1.0, 1.0)}},
                "block_xdata_apps": {
                    ("BLOCK_A", "LAYER_1"): {"ACAD", "CUSTOM_APP"},
                    ("BLOCK_B", "LAYER_1"): set(),
                },
                "layer_block_insertion_counts": {"LAYER_1": 5},
                "layer_entity_counts": {"LAYER_1": 10},
                "layer_unique_color_counts": {"LAYER_1": 0},
                "layer_annotation_counts": {"LAYER_1": 0},
                "annotation_data": {},
                "entity_type_counts": {"INSERT": 5, "LINE": 10},
                "color_analysis_data": [],
                "block_trimming_data": {
                    "BLOCK_A": {
                        "native_width": 10.0,
                        "native_height": 5.0,
                        "vertical_segments": [10.0],
                        "horizontal_segments": [5.0],
                    },
                    "BLOCK_B": {
                        "native_width": 8.0,
                        "native_height": 4.0,
                        "vertical_segments": [8.0],
                        "horizontal_segments": [4.0],
                    },
                },
            }

            output_path = os.path.join(temp_dir, "test_xdata.dxf")
            excel_path = write_excel(result, output_path)

            # Load Excel and verify Block Analysis sheet
            wb = load_workbook(excel_path)
            ws = wb[EXCEL_SHEET_BLOCK_ANALYSIS]

            # Verify 5 columns exist (was 4, now 5 with XDATA Apps)
            assert ws.max_column == 5

            # Verify header is "Block Xdata Apps" (formatted via format_header)
            header_row = [cell.value for cell in ws[1]]
            assert "Block Xdata Apps" in header_row

            # Find the Block Xdata Apps column index
            xdata_col_idx = header_row.index("Block Xdata Apps") + 1

            # Verify BLOCK_A row shows comma-separated XDATA apps
            block_a_found = False
            block_b_found = False
            for row_idx in range(2, ws.max_row + 1):
                block_name = ws.cell(row=row_idx, column=1).value
                if block_name == "BLOCK_A":
                    xdata_value = ws.cell(row=row_idx, column=xdata_col_idx).value
                    # Should contain both apps in sorted order
                    assert xdata_value in ["ACAD, CUSTOM_APP", "CUSTOM_APP, ACAD"]
                    block_a_found = True
                elif block_name == "BLOCK_B":
                    xdata_value = ws.cell(row=row_idx, column=xdata_col_idx).value
                    # Should show "-" for no XDATA
                    assert xdata_value == "-"
                    block_b_found = True

            assert block_a_found, "BLOCK_A not found in Block Analysis sheet"
            assert block_b_found, "BLOCK_B not found in Block Analysis sheet"

    def test_all_sheets_frozen_panes(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that frozen panes are applied to all four sheets."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify frozen panes on Block Analysis sheet
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.freeze_panes is not None
        assert ws_blocks.freeze_panes == "A2"

        # Verify frozen panes on Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.freeze_panes is not None
        assert ws_layers.freeze_panes == "A2"

        # Verify frozen panes on Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.freeze_panes is not None
        assert ws_entities.freeze_panes == "A2"

        # Verify frozen panes on Block Geometry Analysis sheet
        ws_geometry = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]
        assert ws_geometry.freeze_panes is not None
        assert ws_geometry.freeze_panes == "A2"

    def test_frozen_panes_with_empty_data(self, temp_dir: str) -> None:
        """Test that frozen panes are applied even with headers-only sheets."""
        empty_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {},
        }
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(empty_data, output_path)

        wb = load_workbook(excel_path)

        # Verify all sheets have frozen panes even with no data
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.freeze_panes == "A2"

        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.freeze_panes == "A2"

        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.freeze_panes == "A2"

        ws_geometry = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]
        assert ws_geometry.freeze_panes == "A2"

    def test_frozen_panes_position(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that frozen panes cell reference is exactly A2 (freeze row 1)."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify exact frozen pane position for all sheets
        assert wb[EXCEL_SHEET_BLOCK_ANALYSIS].freeze_panes == "A2"
        assert wb[EXCEL_SHEET_LAYER_ANALYSIS].freeze_panes == "A2"
        assert wb[EXCEL_SHEET_ENTITY_SUMMARY].freeze_panes == "A2"
        assert wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS].freeze_panes == "A2"


class TestNegativeScaleDetection:
    """Test suite for the _has_negative_scale_in_set helper function."""

    def test_has_negative_scale_x_with_negatives(self) -> None:
        """Test detection of negative X scales."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, 1.0), (-1.0, 1.0)}
        assert _has_negative_scale_in_set(scale_set, "x") is True

    def test_has_negative_scale_x_without_negatives(self) -> None:
        """Test returns False for all positive X scales."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, 1.0), (2.0, 1.0)}
        assert _has_negative_scale_in_set(scale_set, "x") is False

    def test_has_negative_scale_y_with_negatives(self) -> None:
        """Test detection of negative Y scales."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, -1.0), (1.0, -2.0)}
        assert _has_negative_scale_in_set(scale_set, "y") is True

    def test_has_negative_scale_y_without_negatives(self) -> None:
        """Test returns False for all positive Y scales."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, 1.0), (1.0, 2.0)}
        assert _has_negative_scale_in_set(scale_set, "y") is False

    def test_has_negative_scale_mixed_values(self) -> None:
        """Test set with both positive and negative values."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, 1.0), (-1.0, 1.0), (2.0, -2.0)}
        assert _has_negative_scale_in_set(scale_set, "x") is True
        assert _has_negative_scale_in_set(scale_set, "y") is True

    def test_has_negative_scale_empty_set(self) -> None:
        """Test edge case with empty set raises ValueError."""
        from core.excel_writer import _has_negative_scale_in_set

        with pytest.raises(ValueError, match="scale_set cannot be empty"):
            _has_negative_scale_in_set(set(), "x")

    def test_has_negative_scale_invalid_axis(self) -> None:
        """Test error handling for invalid axis parameter."""
        from core.excel_writer import _has_negative_scale_in_set

        scale_set = {(1.0, 1.0)}
        with pytest.raises(ValueError, match="axis must be 'x' or 'y'"):
            _has_negative_scale_in_set(scale_set, "z")


class TestNegativeScaleTextGeneration:
    """Test suite for scale text generation with negative values."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_scale_text_varies_with_negatives(self, temp_dir: str) -> None:
        """Test that 'VARIES (-)' is displayed when variance exists with negative values."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {
                "TEST": {(1.0, 1.0), (-1.0, 1.0)}
            },  # X varies with negative
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES (-)"

    def test_scale_text_varies_without_negatives(self, temp_dir: str) -> None:
        """Test that 'VARIES' is displayed when variance exists with all positive values."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {
                "TEST": {(1.0, 1.0), (2.0, 1.0)}
            },  # X varies, all positive
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES"

    def test_scale_text_single_negative_value(self, temp_dir: str) -> None:
        """Test that -1.0 is displayed as numeric when scale is consistent negative."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {"TEST": {(-1.0, 1.0)}},  # Consistent negative X scale
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == -1.0

    def test_scale_text_single_positive_value(self, temp_dir: str) -> None:
        """Test that 1.0 is displayed as numeric when scale is consistent positive."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {"TEST": {(1.0, 1.0)}},  # Consistent positive scale
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == 1.0

    def test_scale_text_x_varies_negative_y_consistent(self, temp_dir: str) -> None:
        """Test mixed scenario: X varies with negatives, Y consistent."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {
                "TEST": {(1.0, 2.0), (-1.0, 2.0)}
            },  # X varies with negatives, Y consistent
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES (-)"
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == 2.0

    def test_scale_text_both_vary_one_negative(self, temp_dir: str) -> None:
        """Test both axes vary but only one has negatives."""
        data: ExtractionResult = {
            "block_counts": {"TEST": 2},
            "block_entities": {"TEST": 10},
            "block_layer_pairs": {("TEST", "0"): 2},
            "block_rotation_counts": {},
            "block_scale_data": {
                "TEST": {(1.0, 1.0), (-1.0, 2.0)}
            },  # Both vary, X has negative
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"0": 2},
            "layer_entity_counts": {"0": 20},
            "layer_unique_color_counts": {"0": 0},
            "layer_annotation_counts": {"0": 0},
            "annotation_data": {},
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {
                "TEST": {
                    "native_width": 10.0,
                    "native_height": 10.0,
                    "vertical_segments": [],
                    "horizontal_segments": [],
                }
            },
        }

        output_path = os.path.join(temp_dir, "test.dwg")
        excel_path = write_excel(data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES (-)"
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_SCALE_Y)] == "VARIES"


class TestNegativeScaleIntegration:
    """Integration tests using the negative_scale_test.dxf asset."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_negative_scale_test_dxf_end_to_end(self, temp_dir: str) -> None:
        """Test end-to-end flow with negative_scale_test.dxf verifying all four scenarios."""
        from core.constants import (
            EXCEL_FILL_COLOR_SCALE_NEGATIVE,
            EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
            EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
        )
        from core.extractor import extract_blocks

        # Path to test asset
        test_dxf_path = (
            Path(__file__).parent.parent / "assets" / "negative_scale_test.dxf"
        )

        # Extract data from test DXF
        result = extract_blocks(str(test_dxf_path))

        # Verify block_scale_data contains expected scale sets
        assert "VARY_POSITIVE" in result["block_scale_data"]
        assert "MIRROR_CONSISTENT" in result["block_scale_data"]
        assert "VARY_NEGATIVE" in result["block_scale_data"]
        assert "NORMAL" in result["block_scale_data"]

        # Verify scale sets
        vary_positive_scales = result["block_scale_data"]["VARY_POSITIVE"]
        assert (1.0, 1.0) in vary_positive_scales
        assert (2.0, 1.0) in vary_positive_scales

        mirror_scales = result["block_scale_data"]["MIRROR_CONSISTENT"]
        assert (-1.0, 1.0) in mirror_scales

        vary_negative_scales = result["block_scale_data"]["VARY_NEGATIVE"]
        assert (1.0, 1.0) in vary_negative_scales
        assert (-1.0, 1.0) in vary_negative_scales

        normal_scales = result["block_scale_data"]["NORMAL"]
        assert (1.0, 1.0) in normal_scales

        # Generate Excel file
        output_path = os.path.join(temp_dir, "negative_scale_test.dxf")
        excel_path = write_excel(result, output_path)

        # Load Excel and verify scale text values
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Find rows by block name
        vary_positive_row = df[
            df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VARY_POSITIVE"
        ].iloc[0]
        mirror_row = df[
            df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "MIRROR_CONSISTENT"
        ].iloc[0]
        vary_negative_row = df[
            df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VARY_NEGATIVE"
        ].iloc[0]
        normal_row = df[df[format_header(EXCEL_COLUMN_BLOCK_NAME)] == "NORMAL"].iloc[0]

        # Verify scale text values
        assert vary_positive_row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES"
        assert mirror_row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == -1.0
        assert (
            vary_negative_row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == "VARIES (-)"
        )
        assert normal_row[format_header(EXCEL_COLUMN_BLOCK_SCALE_X)] == 1.0

        # Load workbook to verify highlighting
        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Find row numbers for each block (rows are 1-indexed, with header at row 1)
        row_mapping = {}
        for row_idx in range(2, ws.max_row + 1):
            block_name = ws.cell(row=row_idx, column=1).value
            if block_name:
                row_mapping[block_name] = row_idx

        # Verify highlighting colors
        # VARY_POSITIVE should have yellow fill
        vary_positive_row_idx = row_mapping["VARY_POSITIVE"]
        vary_positive_fill = ws.cell(row=vary_positive_row_idx, column=1).fill
        assert (
            vary_positive_fill.start_color.rgb
            == EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE
        ), "VARY_POSITIVE should have yellow fill"

        # MIRROR_CONSISTENT should have orange fill
        mirror_row_idx = row_mapping["MIRROR_CONSISTENT"]
        mirror_fill = ws.cell(row=mirror_row_idx, column=1).fill
        assert mirror_fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE, (
            "MIRROR_CONSISTENT should have orange fill"
        )

        # VARY_NEGATIVE should have red fill
        vary_negative_row_idx = row_mapping["VARY_NEGATIVE"]
        vary_negative_fill = ws.cell(row=vary_negative_row_idx, column=1).fill
        assert (
            vary_negative_fill.start_color.rgb
            == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE
        ), "VARY_NEGATIVE should have red fill"

        # NORMAL should have no fill (default)
        normal_row_idx = row_mapping["NORMAL"]
        normal_fill = ws.cell(row=normal_row_idx, column=1).fill
        assert (
            normal_fill.fill_type is None or normal_fill.start_color.rgb == "00000000"
        ), "NORMAL should not have highlighting"


class TestAnnotationsAnalysisSheet:
    """Test suite for Annotations Analysis sheet generation."""

    @pytest.fixture
    def temp_dir(self) -> Iterator[str]:
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def annotation_extraction_data(self) -> ExtractionResult:
        """Provide sample extraction data with annotations."""
        return {
            "block_counts": {"VALVE": 5},
            "block_entities": {"VALVE": 8},
            "block_layer_pairs": {("VALVE", "Layer1"): 5},
            "block_rotation_counts": {("VALVE", "Layer1", "0"): 5},
            "block_scale_data": {"VALVE": {(1.0, 1.0)}},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {"Layer1": 5},
            "layer_entity_counts": {"Layer1": 25},
            "layer_unique_color_counts": {"Layer1": 2},
            "layer_annotation_counts": {"Layer1": 10},
            "annotation_data": {
                ("Sample Text", "TEXT", "Layer1", 255, 0, 0): 3,
                ("Another Text", "MTEXT", "Layer2", 0, 255, 0): 2,
                ("Third Text", "TEXT", "Layer1", 0, 0, 255): 1,
            },
            "entity_type_counts": {"INSERT": 5, "LINE": 20},
            "color_analysis_data": [],
            "block_trimming_data": {
                "VALVE": {
                    "native_width": 10.0,
                    "native_height": 5.0,
                    "vertical_segments": [10.0],
                    "horizontal_segments": [5.0],
                }
            },
        }

    def test_annotations_analysis_sheet_exists(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that Annotations Analysis sheet is created."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_ANNOTATIONS_ANALYSIS in wb.sheetnames

    def test_annotations_analysis_sheet_columns(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that Annotations Analysis sheet has correct column structure."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS)

        # Verify 8 columns in correct order
        from core.constants import (
            EXCEL_COLUMN_ANNOTATION_COLOR_B,
            EXCEL_COLUMN_ANNOTATION_COLOR_G,
            EXCEL_COLUMN_ANNOTATION_COLOR_R,
            EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE,
            EXCEL_COLUMN_ANNOTATION_CONTENTS,
            EXCEL_COLUMN_ANNOTATION_COUNT,
            EXCEL_COLUMN_ANNOTATION_LAYER_NAME,
            EXCEL_COLUMN_ANNOTATION_TYPE,
        )

        expected_columns = [
            format_header(EXCEL_COLUMN_ANNOTATION_CONTENTS),
            format_header(EXCEL_COLUMN_ANNOTATION_TYPE),
            format_header(EXCEL_COLUMN_ANNOTATION_LAYER_NAME),
            format_header(EXCEL_COLUMN_ANNOTATION_COLOR_R),
            format_header(EXCEL_COLUMN_ANNOTATION_COLOR_G),
            format_header(EXCEL_COLUMN_ANNOTATION_COLOR_B),
            format_header(EXCEL_COLUMN_ANNOTATION_COLOR_SAMPLE),
            format_header(EXCEL_COLUMN_ANNOTATION_COUNT),
        ]

        assert list(df.columns) == expected_columns
        assert len(df.columns) == 8

    def test_annotations_analysis_sheet_data_accuracy(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that annotation data is correctly written to sheet."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS)

        # Verify we have 3 data rows
        assert len(df) == 3

        # Verify data values (check first row which should be sorted by count desc)
        from core.constants import (
            EXCEL_COLUMN_ANNOTATION_COLOR_R,
            EXCEL_COLUMN_ANNOTATION_CONTENTS,
            EXCEL_COLUMN_ANNOTATION_COUNT,
            EXCEL_COLUMN_ANNOTATION_TYPE,
        )

        # First row should be "Sample Text" with count=3 (highest count)
        first_row = df.iloc[0]
        assert (
            first_row[format_header(EXCEL_COLUMN_ANNOTATION_CONTENTS)] == "Sample Text"
        )
        assert first_row[format_header(EXCEL_COLUMN_ANNOTATION_TYPE)] == "TEXT"
        assert first_row[format_header(EXCEL_COLUMN_ANNOTATION_COUNT)] == 3
        assert first_row[format_header(EXCEL_COLUMN_ANNOTATION_COLOR_R)] == 255

    def test_annotations_analysis_sheet_sorting(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that annotations are sorted by count descending."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS)

        from core.constants import EXCEL_COLUMN_ANNOTATION_COUNT

        # Verify counts are in descending order
        counts = df[format_header(EXCEL_COLUMN_ANNOTATION_COUNT)].tolist()
        assert counts == sorted(counts, reverse=True)
        assert counts == [3, 2, 1]

    def test_annotations_analysis_sheet_empty_data(self, temp_dir: str) -> None:
        """Test Annotations Analysis sheet with no annotation data."""
        empty_data: ExtractionResult = {
            "block_counts": {},
            "block_entities": {},
            "block_layer_pairs": {},
            "block_rotation_counts": {},
            "block_scale_data": {},
            "block_xdata_apps": {},
            "layer_block_insertion_counts": {},
            "layer_entity_counts": {},
            "layer_unique_color_counts": {},
            "layer_annotation_counts": {},
            "annotation_data": {},  # Empty annotations
            "entity_type_counts": {},
            "color_analysis_data": [],
            "block_trimming_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 8

    def test_layer_analysis_uses_annotation_count_column(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that Layer Analysis sheet uses renamed layer_annotation_count column."""
        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_LAYER_ANALYSIS)

        # Verify column header is "Layer Annotation Count" (formatted)
        from core.constants import EXCEL_COLUMN_LAYER_ANNOTATION_COUNT

        expected_header = format_header(EXCEL_COLUMN_LAYER_ANNOTATION_COUNT)
        assert expected_header in df.columns
        assert expected_header == "Layer Annotation Count"

        # Verify data values match layer_annotation_counts from input
        layer1_row = df[df[format_header(EXCEL_COLUMN_LAYER_NAME)] == "Layer1"].iloc[0]
        assert layer1_row[expected_header] == 10

    def test_annotations_analysis_integration_with_real_data(
        self, temp_dir: str
    ) -> None:
        """Integration test with real annotation_test.dxf file."""
        from core.extractor import extract_blocks

        result = extract_blocks("app/tests/assets/annotation_test.dxf")
        output_path = os.path.join(temp_dir, "annotation_test.dxf")
        excel_path = write_excel(result, output_path)

        # Verify sheet exists and has data
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ANNOTATIONS_ANALYSIS)
        assert len(df) > 0  # Should have annotation data

        # Verify all columns present
        assert len(df.columns) == 8

        # Verify sorting
        from core.constants import EXCEL_COLUMN_ANNOTATION_COUNT

        counts = df[format_header(EXCEL_COLUMN_ANNOTATION_COUNT)].tolist()
        assert counts == sorted(counts, reverse=True)

    def test_five_sheets_created(
        self, temp_dir: str, annotation_extraction_data: ExtractionResult
    ) -> None:
        """Test that exactly 6 sheets are created including Color Analysis."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dwg")
        excel_path = write_excel(annotation_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify exactly 6 sheets
        assert len(wb.sheetnames) == 6

        # Verify all expected sheet names
        assert EXCEL_SHEET_BLOCK_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ANNOTATIONS_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_COLOR_ANALYSIS in wb.sheetnames
