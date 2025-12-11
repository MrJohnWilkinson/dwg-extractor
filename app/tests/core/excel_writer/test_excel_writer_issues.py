"""
Unit tests for the excel_writer module - Extraction Issues sheet.

This test suite validates:
- Extraction Issues sheet creation and headers
- Data content and formatting
- Auto-filter, frozen panes, column widths
- Yellow highlighting for issue rows
- Sheet positioning (last sheet)
"""

import os

import pandas as pd
from openpyxl import load_workbook

from core.excel_writer import write_excel
from core.extractor import ExtractionResult


class TestExtractionIssuesSheet:
    """Test suite for the Extraction Issues Excel sheet."""

    def test_extraction_issues_sheet_exists(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet exists in the workbook."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)
        assert EXCEL_SHEET_EXTRACTION_ISSUES in wb.sheetnames

    def test_extraction_issues_sheet_headers(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet has correct headers."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_EXTRACTION_ISSUES)

        expected_columns = [
            "Issue Type",
            "Issue Block Name",
            "Issue Layer Name",
            "Issue Insertion Count",
            "Issue Details",
        ]
        assert list(df.columns) == expected_columns

    def test_extraction_issues_sheet_contains_data(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet contains unresolved blocks."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_EXTRACTION_ISSUES)

        # Should have 2 rows of data
        assert len(df) == 2

        # Verify first row data
        assert df.iloc[0]["Issue Type"] == "Unresolved Anonymous Block"
        assert df.iloc[0]["Issue Block Name"] == "*U1"
        assert df.iloc[0]["Issue Layer Name"] == "Layer1"
        assert df.iloc[0]["Issue Insertion Count"] == 5
        assert "AcDbBlockRepBTag" in df.iloc[0]["Issue Details"]

    def test_extraction_issues_sheet_empty_when_no_issues(
        self, temp_dir: str, no_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet is empty when no issues."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(no_issues_data, output_path)

        df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_EXTRACTION_ISSUES)

        # Should have headers but no data rows
        assert len(df) == 0
        # Headers should still be present
        assert "Issue Type" in df.columns

    def test_extraction_issues_sheet_has_autofilter(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet has auto-filter enabled."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_EXTRACTION_ISSUES]

        # Verify auto-filter is applied
        assert ws.auto_filter.ref is not None

    def test_extraction_issues_sheet_has_frozen_panes(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet has frozen header row."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_EXTRACTION_ISSUES]

        # Verify frozen panes at B2 (header row and first column)
        assert ws.freeze_panes == "B2"

    def test_extraction_issues_sheet_column_widths(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet has appropriate column widths."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_EXTRACTION_ISSUES]

        # Verify column widths are set
        assert ws.column_dimensions["A"].width == 30  # issue_type
        assert ws.column_dimensions["B"].width == 30  # issue_block_name
        assert ws.column_dimensions["C"].width == 25  # issue_layer_name
        assert ws.column_dimensions["D"].width == 20  # issue_insertion_count
        assert ws.column_dimensions["E"].width == 50  # issue_details

    def test_extraction_issues_sheet_has_yellow_highlighting(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet data rows have yellow highlighting."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)
        ws = wb[EXCEL_SHEET_EXTRACTION_ISSUES]

        # Check that row 2 (first data row) has yellow fill
        # Yellow color is FFFFFF00
        cell_a2 = ws.cell(row=2, column=1)
        assert cell_a2.fill.fgColor is not None

    def test_extraction_issues_sheet_position(
        self, temp_dir: str, extraction_issues_data: ExtractionResult
    ) -> None:
        """Test that Extraction Issues sheet is at position 8 (index 7)."""
        from core.constants import EXCEL_SHEET_EXTRACTION_ISSUES

        output_path = os.path.join(temp_dir, "test_drawing.dxf")
        excel_path = write_excel(extraction_issues_data, output_path)

        wb = load_workbook(excel_path)

        # Extraction Issues should be at index 7 (Sheet 8, after All Blocks was added)
        assert EXCEL_SHEET_EXTRACTION_ISSUES in wb.sheetnames
        assert wb.sheetnames.index(EXCEL_SHEET_EXTRACTION_ISSUES) == 7
