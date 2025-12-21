"""
Unit tests for the excel_writer module - core functionality.

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

import pandas as pd
import pytest
from openpyxl import load_workbook

from core.constants import (
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT,
    EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH,
    EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
    EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_HORIZONTAL_SEGMENTS,
    EXCEL_COLUMN_BLOCK_INSERTION_COUNT,
    EXCEL_COLUMN_BLOCK_LAYER_NAME,
    EXCEL_COLUMN_BLOCK_NAME,
    EXCEL_COLUMN_BLOCK_NATIVE_HEIGHT,
    EXCEL_COLUMN_BLOCK_NATIVE_WIDTH,
    EXCEL_COLUMN_BLOCK_POLYGON_COUNT,
    EXCEL_COLUMN_BLOCK_ROTATION_0,
    EXCEL_COLUMN_BLOCK_ROTATION_90,
    EXCEL_COLUMN_BLOCK_ROTATION_180,
    EXCEL_COLUMN_BLOCK_ROTATION_270,
    EXCEL_COLUMN_BLOCK_ROTATION_OTHER,
    EXCEL_COLUMN_BLOCK_SCALE_X,
    EXCEL_COLUMN_BLOCK_SCALE_Y,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT,
    EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP,
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
    EXCEL_SHEET_ALL_BLOCKS,
    EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
    EXCEL_SHEET_BLOCK_ANALYSIS,
    EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
    EXCEL_SHEET_ENTITY_SUMMARY,
    EXCEL_SHEET_LAYER_ANALYSIS,
)
from core.excel_formatting import format_header
from core.excel_writer import write_excel
from core.extractor import ExtractionResult
from core.types import BlockLayerKey, BlockRotationKey


class TestExcelWriter:
    """Test suite for the write_excel function."""

    def test_write_excel_nine_sheets(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that nine sheets are created with correct names."""
        from core.constants import (
            EXCEL_SHEET_BLOCK_DEFINITIONS,
            EXCEL_SHEET_COLOR_ANALYSIS,
            EXCEL_SHEET_EXTRACTION_ISSUES,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load and verify sheet names
        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_ALL_BLOCKS in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_ANNOTATIONS_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_COLOR_ANALYSIS in wb.sheetnames
        assert EXCEL_SHEET_EXTRACTION_ISSUES in wb.sheetnames
        assert EXCEL_SHEET_BLOCK_DEFINITIONS in wb.sheetnames
        assert len(wb.sheetnames) == 9

    def test_block_analysis_sheet_simplified(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Analysis sheet has correct simplified structure (5 columns, no rotations)."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")

        with pytest.raises(ValueError, match="extraction_data cannot be None"):
            write_excel(None, output_path)  # type: ignore[arg-type]

    def test_block_trimming_analysis_sheet_exists(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet exists."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames

    def test_block_geometry_analysis_sheet_consolidated(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Geometry Analysis sheet has all 22 columns consolidated."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT),
        ]

        assert list(df.columns) == expected_columns

        # Verify exactly 22 columns (13 original + 9 content zone)
        assert len(df.columns) == 22

        # Verify sort by block_name alphabetical
        block_names = df[format_header(EXCEL_COLUMN_BLOCK_NAME)].tolist()
        assert block_names == sorted(block_names)

    def test_block_trimming_analysis_data_types(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test Block Trimming Analysis sheet has correct data types."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 22

    def test_block_trimming_analysis_auto_filter(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Block Trimming Analysis sheet has auto-filter applied."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        """Test that empty block_layer_pairs creates sheet with all 22 column headers."""
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
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(empty_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should have headers but no data rows
        assert len(df) == 0

        # Verify all 22 column headers (formatted)
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
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT),
        ]
        assert list(df.columns) == expected_columns

    def test_block_trimming_analysis_missing_geometry(self, temp_dir: str) -> None:
        """Test that blocks in block_layer_pairs but not in block_trimming_data are skipped gracefully."""
        # Data with a block-layer pair that has no geometry data
        data_with_missing_geometry: ExtractionResult = {
            "block_counts": {"VALVE": 10, "ANONYMOUS": 5},
            "block_entities": {"VALVE": 8, "ANONYMOUS": 0},
            "block_layer_pairs": {
                BlockLayerKey(block_name="VALVE", layer_name="Layer1"): 10,
                BlockLayerKey(
                    block_name="ANONYMOUS", layer_name="Layer1"
                ): 5,  # This block has no geometry data
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
            "extraction_issues": [],
            "block_trimming_data": {
                "VALVE": {
                    "native_width": 100.0,
                    "native_height": 50.0,
                    "vertical_segments": [10.0, 80.0, 10.0],
                    "horizontal_segments": [5.0, 40.0, 5.0],
                }
                # ANONYMOUS block intentionally missing from block_trimming_data
            },
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(data_with_missing_geometry, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS)

        # Should only have VALVE row, ANONYMOUS should be skipped
        assert len(df) == 1
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_NAME)] == "VALVE"
        assert df.iloc[0][format_header(EXCEL_COLUMN_BLOCK_LAYER_NAME)] == "Layer1"

    def test_write_excel_value_error_invalid_data(self, temp_dir: str) -> None:
        """Test that write_excel raises exception for invalid extraction data structure."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")

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
        invalid_path = os.path.join(temp_dir, "nonexistent_dir", "test.dxf")

        # Verify exception is raised for invalid path
        with pytest.raises(Exception):
            write_excel(sample_extraction_data, invalid_path)

    def test_constants_match_dataframe_columns(self, temp_dir: str) -> None:
        """Test that constants.py values exactly match DataFrame column names in all sheets."""
        from core.extractor import extract_blocks

        # Extract real data from sample file
        extraction_data = extract_blocks("app/tests/assets/sample_drawing.dxf")

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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

        # Block Geometry Analysis sheet - 22 columns (13 original + 9 content zone)
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
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP),
            format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH),
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT),
            format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT),
            format_header(EXCEL_COLUMN_BLOCK_FILTERED_POLYGON_COUNT),
        ]

    def test_spec_010_consolidated_geometry_sheet(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test spec 010: Block Geometry Analysis sheet has consolidated 22 columns with scales, rotations, and content zone."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        df_geometry = pd.read_excel(
            excel_path, sheet_name=EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS
        )
        df_blocks = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_ANALYSIS)

        # Verify Block Geometry Analysis has exactly 22 columns (13 original + 9 content zone)
        assert len(df_geometry.columns) == 22

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
        # VALVE: {(1.0, 1.0), (-1.0, 1.0)} - X varies with negatives -> red
        # PIPE: {(1.0, -1.0)} - Consistent negative Y -> orange
        # TAG: {(-1.0, -1.0)} - Consistent negative X and Y -> orange
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
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
                    BlockLayerKey(block_name="BLOCK_A", layer_name="LAYER_1"): 3,
                    BlockLayerKey(block_name="BLOCK_B", layer_name="LAYER_1"): 2,
                },
                "block_rotation_counts": {
                    BlockRotationKey(
                        block_name="BLOCK_A",
                        layer_name="LAYER_1",
                        rotation_category="0",
                    ): 3,
                    BlockRotationKey(
                        block_name="BLOCK_B",
                        layer_name="LAYER_1",
                        rotation_category="0",
                    ): 2,
                },
                "block_scale_data": {"BLOCK_A": {(1.0, 1.0)}, "BLOCK_B": {(1.0, 1.0)}},
                "block_xdata_apps": {
                    BlockLayerKey(block_name="BLOCK_A", layer_name="LAYER_1"): {
                        "ACAD",
                        "CUSTOM_APP",
                    },
                    BlockLayerKey(block_name="BLOCK_B", layer_name="LAYER_1"): set(),
                },
                "layer_block_insertion_counts": {"LAYER_1": 5},
                "layer_entity_counts": {"LAYER_1": 10},
                "layer_unique_color_counts": {"LAYER_1": 0},
                "layer_annotation_counts": {"LAYER_1": 0},
                "annotation_data": {},
                "entity_type_counts": {"INSERT": 5, "LINE": 10},
                "color_analysis_data": [],
                "extraction_issues": [],
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
                "block_content_zone_data": {},
                "all_block_definitions": {},
                "nested_block_parents": {},
                "block_attribute_data": {},
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
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify frozen panes on Block Analysis sheet (B2 freezes header row and first column)
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.freeze_panes is not None
        assert ws_blocks.freeze_panes == "B2"

        # Verify frozen panes on Layer Analysis sheet
        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.freeze_panes is not None
        assert ws_layers.freeze_panes == "B2"

        # Verify frozen panes on Entity Summary sheet
        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.freeze_panes is not None
        assert ws_entities.freeze_panes == "B2"

        # Verify frozen panes on Block Geometry Analysis sheet
        ws_geometry = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]
        assert ws_geometry.freeze_panes is not None
        assert ws_geometry.freeze_panes == "B2"

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
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(empty_data, output_path)

        wb = load_workbook(excel_path)

        # Verify all sheets have frozen panes even with no data (B2 freezes header row and first column)
        ws_blocks = wb[EXCEL_SHEET_BLOCK_ANALYSIS]
        assert ws_blocks.freeze_panes == "B2"

        ws_layers = wb[EXCEL_SHEET_LAYER_ANALYSIS]
        assert ws_layers.freeze_panes == "B2"

        ws_entities = wb[EXCEL_SHEET_ENTITY_SUMMARY]
        assert ws_entities.freeze_panes == "B2"

        ws_geometry = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]
        assert ws_geometry.freeze_panes == "B2"

    def test_frozen_panes_position(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that frozen panes cell reference is exactly B2 (freeze row 1 and column A)."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)

        # Verify exact frozen pane position for all sheets (B2 freezes header row and first column)
        assert wb[EXCEL_SHEET_BLOCK_ANALYSIS].freeze_panes == "B2"
        assert wb[EXCEL_SHEET_LAYER_ANALYSIS].freeze_panes == "B2"
        assert wb[EXCEL_SHEET_ENTITY_SUMMARY].freeze_panes == "B2"
        assert wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS].freeze_panes == "B2"


class TestContentZoneExcelOutput:
    """Tests for content zone columns in Excel output."""

    def test_content_zone_columns_in_output(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Excel output includes all 5 content zone columns."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Check headers include content zone columns
        headers = [cell.value for cell in ws[1]]
        assert format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_RIGHT) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_TOP) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_BOTTOM) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED) in headers

    def test_content_zone_values_populated(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Content zone values are populated in Excel output."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        trim_left_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_SUGGESTED_TRIM_LEFT)) + 1
        )
        detected_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED)) + 1
        )

        # Find VALVE row (should have content zone detected)
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1
        valve_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "VALVE":
                valve_row = row_idx
                break

        assert valve_row is not None, "VALVE row not found"
        assert ws.cell(row=valve_row, column=trim_left_col).value == 10.0
        assert ws.cell(row=valve_row, column=detected_col).value == "TRUE"

    def test_detection_flag_false_for_undetected(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Content zone detected shows FALSE when detection failed."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        detected_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED)) + 1
        )
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1

        # Find TAG row (should have content zone NOT detected based on fixture)
        tag_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "TAG":
                tag_row = row_idx
                break

        assert tag_row is not None, "TAG row not found"
        assert ws.cell(row=tag_row, column=detected_col).value == "FALSE"

    def test_content_zone_column_count(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Block Geometry Analysis sheet has 22 columns (13 original + 9 content zone)."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        headers = [cell.value for cell in ws[1]]
        # Filter out None values for accurate count
        headers = [h for h in headers if h is not None]
        assert len(headers) == 22

    def test_new_content_zone_columns_in_headers(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """New content zone columns appear in DataFrame headers with correct Title Case formatting."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get headers
        headers = [cell.value for cell in ws[1]]

        # Verify new columns appear with correct formatting
        assert format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT) in headers
        assert format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT) in headers

        # Verify column order: width, height, polygon_count appear after content_zone_detected
        detected_idx = headers.index(
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED)
        )
        width_idx = headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH))
        height_idx = headers.index(
            format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT)
        )
        poly_idx = headers.index(format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT))

        assert width_idx == detected_idx + 1
        assert height_idx == detected_idx + 2
        assert poly_idx == detected_idx + 3

    def test_content_zone_width_height_populated_when_detected(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Width/height values are populated when content zone is detected."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1
        width_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH)) + 1
        )
        height_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT)) + 1
        )
        detected_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED)) + 1
        )

        # Find VALVE row (should have content zone detected)
        valve_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "VALVE":
                valve_row = row_idx
                break

        assert valve_row is not None, "VALVE row not found"
        assert ws.cell(row=valve_row, column=detected_col).value == "TRUE"
        assert ws.cell(row=valve_row, column=width_col).value == 80.0
        assert ws.cell(row=valve_row, column=height_col).value == 40.0

    def test_content_zone_width_height_empty_when_not_detected(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Width/height show empty string when content zone not detected."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1
        width_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_WIDTH)) + 1
        )
        height_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_HEIGHT)) + 1
        )
        detected_col = (
            headers.index(format_header(EXCEL_COLUMN_BLOCK_CONTENT_ZONE_DETECTED)) + 1
        )

        # Find TAG row (should have content zone NOT detected)
        tag_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "TAG":
                tag_row = row_idx
                break

        assert tag_row is not None, "TAG row not found"
        assert ws.cell(row=tag_row, column=detected_col).value == "FALSE"
        # Empty string in Excel becomes None when loaded
        assert ws.cell(row=tag_row, column=width_col).value is None
        assert ws.cell(row=tag_row, column=height_col).value is None

    def test_polygon_count_always_present(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Polygon count appears for all rows."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        poly_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT)) + 1

        # Check that all data rows have polygon count (either 0 or a count)
        for row_idx in range(2, ws.max_row + 1):
            poly_value = ws.cell(row=row_idx, column=poly_col).value
            # Value should be an integer (0 or positive)
            assert isinstance(poly_value, int) or poly_value is None or poly_value == ""

    def test_polygon_count_zero_when_no_polygons(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Polygon count displays 0 when no polygons found."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1
        poly_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT)) + 1

        # Find TAG row (fixture has polygon_count=0)
        tag_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "TAG":
                tag_row = row_idx
                break

        assert tag_row is not None, "TAG row not found"
        assert ws.cell(row=tag_row, column=poly_col).value == 0

    def test_polygon_count_value_when_polygons_found(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Polygon count displays actual count when polygons found."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS]

        # Get header column indices
        headers = [cell.value for cell in ws[1]]
        block_name_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_NAME)) + 1
        poly_col = headers.index(format_header(EXCEL_COLUMN_BLOCK_POLYGON_COUNT)) + 1

        # Find VALVE row (fixture has polygon_count=2)
        valve_row = None
        for row_idx in range(2, ws.max_row + 1):
            if ws.cell(row=row_idx, column=block_name_col).value == "VALVE":
                valve_row = row_idx
                break

        assert valve_row is not None, "VALVE row not found"
        assert ws.cell(row=valve_row, column=poly_col).value == 2


class TestAllBlocksSheetIntegration:
    """Integration tests for All Blocks sheet in write_excel flow."""

    def test_write_excel_creates_all_blocks_sheet(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that write_excel creates All Blocks sheet in the workbook."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load and verify All Blocks sheet exists
        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_ALL_BLOCKS in wb.sheetnames

        # Verify sheet is not empty (has headers at minimum)
        ws = wb[EXCEL_SHEET_ALL_BLOCKS]
        assert ws.max_row >= 1  # At least header row exists
        assert ws.max_column == 29  # All 29 columns should be present

    def test_write_excel_all_blocks_is_first_sheet(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that All Blocks is the first (leftmost) sheet in the workbook."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load workbook and verify sheet order
        wb = load_workbook(excel_path)
        assert wb.sheetnames[0] == EXCEL_SHEET_ALL_BLOCKS

    def test_write_excel_sheet_order(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that sheets are in the correct order."""
        from core.constants import (
            EXCEL_SHEET_BLOCK_DEFINITIONS,
            EXCEL_SHEET_COLOR_ANALYSIS,
            EXCEL_SHEET_EXTRACTION_ISSUES,
        )

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load workbook and verify sheet order
        wb = load_workbook(excel_path)

        expected_order = [
            EXCEL_SHEET_ALL_BLOCKS,
            EXCEL_SHEET_BLOCK_ANALYSIS,
            EXCEL_SHEET_LAYER_ANALYSIS,
            EXCEL_SHEET_ENTITY_SUMMARY,
            EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS,
            EXCEL_SHEET_ANNOTATIONS_ANALYSIS,
            EXCEL_SHEET_COLOR_ANALYSIS,
            EXCEL_SHEET_EXTRACTION_ISSUES,
            EXCEL_SHEET_BLOCK_DEFINITIONS,
        ]

        assert wb.sheetnames == expected_order

    def test_write_excel_all_blocks_has_correct_columns(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that All Blocks sheet has 29 columns with correct headers."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load All Blocks sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

        # Verify 29 columns
        assert len(df.columns) == 29

        # Verify key column headers exist (formatted)
        headers = list(df.columns)
        assert format_header("block_raw_name") in headers
        assert format_header("block_resolved_name") in headers
        assert format_header("block_insertion_status") in headers
        assert format_header("block_insertion_count") in headers
        assert format_header("block_layer_count") in headers
        assert format_header("block_layer_names") in headers

    def test_write_excel_all_blocks_empty_data(self, temp_dir: str) -> None:
        """Test that empty extraction data creates All Blocks sheet with headers only."""
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
            "extraction_issues": [],
            "block_trimming_data": {},
            "block_content_zone_data": {},
            "all_block_definitions": {},
            "nested_block_parents": {},
            "block_attribute_data": {},
        }

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(empty_data, output_path)

        # Verify file exists
        assert Path(excel_path).exists()

        # Load All Blocks sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_ALL_BLOCKS)

        # Should have headers but no data rows
        assert len(df) == 0
        assert len(df.columns) == 29

    def test_write_excel_all_blocks_formatting_applied(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that formatting is applied to All Blocks sheet."""
        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(sample_extraction_data, output_path)

        # Load workbook and verify formatting
        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_ALL_BLOCKS]

        # Verify auto-filter is applied
        assert ws.auto_filter.ref is not None

        # Verify frozen panes are applied (B2 freezes header row and first column)
        assert ws.freeze_panes == "B2"

        # Verify column widths are set (first column should have a width > 0)
        assert ws.column_dimensions["A"].width > 0


class TestTruncateSegmentString:
    """Tests for _truncate_segment_string helper function."""

    def test_short_string_unchanged(self) -> None:
        """Test that strings under max length are returned unchanged."""
        from core.excel_writer import _truncate_segment_string

        result = _truncate_segment_string("10, 20, 30")
        assert result == "10, 20, 30"

    def test_exact_length_unchanged(self) -> None:
        """Test that strings exactly at max length are returned unchanged."""
        from core.excel_writer import (
            SEGMENT_MAX_DISPLAY_LENGTH,
            _truncate_segment_string,
        )

        exact_string = "a" * SEGMENT_MAX_DISPLAY_LENGTH
        result = _truncate_segment_string(exact_string)
        assert result == exact_string
        assert len(result) == SEGMENT_MAX_DISPLAY_LENGTH

    def test_long_string_truncated(self) -> None:
        """Test that strings over max length are truncated with ellipsis."""
        from core.excel_writer import (
            SEGMENT_MAX_DISPLAY_LENGTH,
            _truncate_segment_string,
        )

        long_string = "a" * 250
        result = _truncate_segment_string(long_string)
        assert len(result) == SEGMENT_MAX_DISPLAY_LENGTH
        assert result.endswith("...")
        assert result == "a" * 197 + "..."

    def test_empty_string(self) -> None:
        """Test that empty string is returned unchanged."""
        from core.excel_writer import _truncate_segment_string

        result = _truncate_segment_string("")
        assert result == ""

    def test_custom_max_length(self) -> None:
        """Test truncation with custom max length."""
        from core.excel_writer import _truncate_segment_string

        result = _truncate_segment_string("0123456789", max_length=8)
        assert result == "01234..."
        assert len(result) == 8

    def test_default_max_length_constant(self) -> None:
        """Test that default max length constant is set correctly."""
        from core.excel_writer import SEGMENT_MAX_DISPLAY_LENGTH

        assert SEGMENT_MAX_DISPLAY_LENGTH == 200
