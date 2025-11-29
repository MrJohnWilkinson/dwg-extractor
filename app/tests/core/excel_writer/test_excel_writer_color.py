"""
Unit tests for the excel_writer module - Color Analysis sheet.

This test suite validates:
- ACI (AutoCAD Color Index) display name mapping
- Color Analysis sheet Excel output with AutoCAD name column
"""

import os

import pandas as pd

from core.excel_writer import write_excel
from core.extractor import ExtractionResult


class TestAciDisplayNameMapping:
    """Test suite for ACI (AutoCAD Color Index) display name mapping."""

    def test_get_aci_display_name_true_color(self) -> None:
        """Test that None returns 'True Color'."""
        from core.excel_writer import _get_aci_display_name

        assert _get_aci_display_name(None) == "True Color"

    def test_get_aci_display_name_byblock(self) -> None:
        """Test that ACI 0 returns 'ByBlock'."""
        from core.excel_writer import _get_aci_display_name

        assert _get_aci_display_name(0) == "ByBlock"

    def test_get_aci_display_name_bylayer(self) -> None:
        """Test that ACI 256 returns 'ByLayer'."""
        from core.excel_writer import _get_aci_display_name

        assert _get_aci_display_name(256) == "ByLayer"

    def test_get_aci_display_name_named_colors(self) -> None:
        """Test that ACI 1-7 return named colors."""
        from core.excel_writer import _get_aci_display_name

        assert _get_aci_display_name(1) == "Red"
        assert _get_aci_display_name(2) == "Yellow"
        assert _get_aci_display_name(3) == "Green"
        assert _get_aci_display_name(4) == "Cyan"
        assert _get_aci_display_name(5) == "Blue"
        assert _get_aci_display_name(6) == "Magenta"
        assert _get_aci_display_name(7) == "White"

    def test_get_aci_display_name_numbered_colors(self) -> None:
        """Test that ACI 8-255 return 'Color N' format."""
        from core.excel_writer import _get_aci_display_name

        assert _get_aci_display_name(8) == "Color 8"
        assert _get_aci_display_name(30) == "Color 30"
        assert _get_aci_display_name(100) == "Color 100"
        assert _get_aci_display_name(220) == "Color 220"
        assert _get_aci_display_name(255) == "Color 255"

    def test_get_aci_display_name_boundary_values(self) -> None:
        """Test boundary values between named and numbered colors."""
        from core.excel_writer import _get_aci_display_name

        # ACI 7 is last named color
        assert _get_aci_display_name(7) == "White"
        # ACI 8 is first numbered color
        assert _get_aci_display_name(8) == "Color 8"


class TestColorAnalysisExcelOutput:
    """Test suite for Color Analysis sheet Excel output with AutoCAD name column."""

    def test_color_analysis_sheet_has_autocad_name_column(
        self, temp_dir: str, color_analysis_data: ExtractionResult
    ) -> None:
        """Test that Color Analysis sheet includes the AutoCAD Name column."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(color_analysis_data, output_path)

        # Load Color Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS)

        # Verify "Color Autocad Name" column exists
        assert "Color Autocad Name" in df.columns

    def test_color_analysis_sheet_column_position(
        self, temp_dir: str, color_analysis_data: ExtractionResult
    ) -> None:
        """Test that AutoCAD Name column appears after Color Sample."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(color_analysis_data, output_path)

        # Load Color Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS)

        # Expected column order (9 columns now)
        expected_columns = [
            "Color Annotation Contents",
            "Color Layer Name",
            "Color Red",
            "Color Green",
            "Color Blue",
            "Color Sample",
            "Color Autocad Name",
            "Color Entity Type",
            "Color Entity Count",
        ]

        assert list(df.columns) == expected_columns

    def test_color_analysis_sheet_aci_values_mapped(
        self, temp_dir: str, color_analysis_data: ExtractionResult
    ) -> None:
        """Test that ACI values are correctly mapped to display names."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(color_analysis_data, output_path)

        # Load Color Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS)

        # Get AutoCAD Name values
        autocad_names = df["Color Autocad Name"].tolist()

        # Should have mapped values
        assert "Red" in autocad_names  # ACI 1
        assert "Yellow" in autocad_names  # ACI 2
        assert "True Color" in autocad_names  # ACI None
        assert "ByLayer" in autocad_names  # ACI 256

    def test_color_analysis_sheet_nine_columns(
        self, temp_dir: str, color_analysis_data: ExtractionResult
    ) -> None:
        """Test that Color Analysis sheet has exactly 9 columns."""
        from core.constants import EXCEL_SHEET_COLOR_ANALYSIS

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(color_analysis_data, output_path)

        # Load Color Analysis sheet
        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_COLOR_ANALYSIS)

        assert len(df.columns) == 9
