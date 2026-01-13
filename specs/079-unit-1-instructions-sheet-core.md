# Feature: Instructions Sheet Core Implementation (Unit 1)

## Feature Description
Implement the core functionality for a static "Instructions" sheet in the Excel output. This sheet explains the color coding used throughout the workbook and describes what each sheet contains. The Instructions sheet will be positioned as the first (leftmost) tab, making it immediately visible when users open the file. This unit covers Steps 1-5 from the parent spec (078-instructions-sheet.md): adding the constant, creating the writer function, creating the formatting function, integrating into write_excel, and ensuring sheet position.

## User Story
As a user reviewing the Excel output
I want an Instructions sheet that explains the color coding and sheet contents
So that I can quickly understand the visual indicators and find the data I need without external documentation

## Problem Statement
The Excel output contains 10 sheets with various color highlights (yellow for scale variance, orange for negative scale, red for variance with negatives, green for nested blocks) but users have no in-document reference to understand what these colors mean. Users must explore multiple tabs to understand what each sheet contains, and there is no quick reference available within the workbook itself.

## Solution Statement
Add a new "Instructions" sheet as the first tab in the Excel workbook containing:
1. A Color Coding section explaining the four highlight colors and their meanings with actual color sample cells
2. A Sheet Descriptions section listing all 10 analysis sheets with brief descriptions

The sheet uses simple formatting (bold headers, appropriate column widths, text wrapping) without auto-filter or freeze panes since it contains static reference content rather than filterable data.

## Relevant Files
Use these files to implement the feature:

### Existing Files to Modify

- `app/core/constants.py`
  - Add `EXCEL_SHEET_INSTRUCTIONS` constant for the new sheet name
  - Located around line 24 with other `EXCEL_SHEET_*` constants
  - Reference existing color constants: `EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE`, `EXCEL_FILL_COLOR_SCALE_NEGATIVE`, `EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE`, `EXCEL_FILL_COLOR_NESTED_BLOCK`

- `app/core/excel_writer.py`
  - Add `_create_instructions_sheet()` function to generate the static content
  - Update `write_excel()` to call the new sheet creation function FIRST
  - Add imports for `EXCEL_SHEET_INSTRUCTIONS` and `_format_instructions_sheet`

- `app/core/excel_formatting.py`
  - Add `_format_instructions_sheet()` function for column widths, bold headers, text wrapping, and color fills
  - Add import for `EXCEL_SHEET_INSTRUCTIONS` constant
  - Note: This function will NOT apply auto-filter or freeze panes (differs from other sheets)

### New Files to Create

- `app/tests/core/excel_writer/test_excel_writer_instructions.py`
  - Unit tests for `_create_instructions_sheet()` function
  - Test sheet creation, content, and position

- `app/tests/core/excel_formatting/test_formatting_instructions.py`
  - Unit tests for `_format_instructions_sheet()` function
  - Test formatting, column widths, bold headers, NO auto-filter, NO freeze panes

## Implementation Plan

### Phase 1: Foundation
Add the sheet name constant to `constants.py` following the existing `EXCEL_SHEET_*` naming pattern. This establishes the sheet identifier used throughout the codebase.

### Phase 2: Core Implementation
1. Create `_create_instructions_sheet()` in `excel_writer.py` that builds a DataFrame with:
   - Color Coding section header row and 4 color description rows (Yellow, Orange, Red, Light Green)
   - Empty separator row
   - Sheet Descriptions section header row and 10 sheet description rows
   - Write to Excel using pandas ExcelWriter

2. Create `_format_instructions_sheet()` in `excel_formatting.py` that applies:
   - Column widths (Column A: 20 for identifiers, Column B: 60 for descriptions)
   - Bold font on section headers ("Color Coding" and "Sheet Descriptions")
   - Text wrapping on Column B (descriptions)
   - Color fills on Column B in the Color Coding section to show actual colors
   - NO auto-filter (static content)
   - NO freeze panes (short, static content)

### Phase 3: Integration
1. Update `write_excel()` to call `_create_instructions_sheet(writer)` BEFORE all other sheet creation calls
2. Update `write_excel()` to call `_format_instructions_sheet(wb)` as the FIRST formatting call after `wb = load_workbook()`
3. Since sheets are ordered by creation in pandas ExcelWriter, creating Instructions first ensures it is the leftmost tab

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Sheet Name Constant
- Open `app/core/constants.py`
- Locate the Excel configuration sheet names section (around line 24, after `EXCEL_SHEET_BLOCK_ANALYSIS`)
- Add the new constant:
```python
EXCEL_SHEET_INSTRUCTIONS: str = "Instructions"
```
- Place it BEFORE `EXCEL_SHEET_BLOCK_ANALYSIS` since Instructions should be the first sheet conceptually

### Step 2: Create Instructions Sheet Writer Function
- Open `app/core/excel_writer.py`
- Add import for `EXCEL_SHEET_INSTRUCTIONS` to the existing constants import block (around line 91-101)
- Create the `_create_instructions_sheet` function after the module-level helper functions and before `write_excel`:

```python
def _create_instructions_sheet(writer: pd.ExcelWriter) -> None:
    """Create the Instructions sheet with color coding legend and sheet descriptions.

    This sheet provides users with:
    - Color Coding section: Explains the four highlight colors used throughout the workbook
    - Sheet Descriptions section: Brief description of each analysis sheet's purpose

    The sheet is created first to ensure it appears as the leftmost tab in Excel.

    Args:
        writer: pandas ExcelWriter object for output
    """
    logger.info("Creating Instructions sheet...")

    # Build rows for the Instructions sheet
    rows = []

    # Section 1: Color Coding
    rows.append({"identifier": "Color Coding", "description": ""})
    rows.append({
        "identifier": "Yellow",
        "description": "Scale variance detected - block has multiple scale values (all positive)"
    })
    rows.append({
        "identifier": "Orange",
        "description": "Negative scale detected - block is mirrored/flipped (consistent negative scale)"
    })
    rows.append({
        "identifier": "Red",
        "description": "Scale variance with negatives - block has varying scales including negative values"
    })
    rows.append({
        "identifier": "Light Green",
        "description": "Nested block - block is used inside another block definition"
    })

    # Empty separator row
    rows.append({"identifier": "", "description": ""})

    # Section 2: Sheet Descriptions
    rows.append({"identifier": "Sheet Descriptions", "description": ""})
    rows.append({
        "identifier": "All Blocks",
        "description": "Consolidated block-centric view with one row per block definition, including geometry, attributes, and insertion data"
    })
    rows.append({
        "identifier": "Block Analysis",
        "description": "Simplified inventory showing block-layer pairs with insertion counts and entity counts"
    })
    rows.append({
        "identifier": "Layer Analysis",
        "description": "Layer-based metrics including block insertions, entity counts, colors, and annotations per layer"
    })
    rows.append({
        "identifier": "Entity Summary",
        "description": "Global entity type counts across the entire drawing (INSERT, LINE, CIRCLE, etc.)"
    })
    rows.append({
        "identifier": "Block Geometry Analysis",
        "description": "Detailed transformation data per block-layer pair: rotations, scales, dimensions, and content zones"
    })
    rows.append({
        "identifier": "Annotations Analysis",
        "description": "TEXT and MTEXT annotations with contents, type, layer, color, and occurrence counts"
    })
    rows.append({
        "identifier": "Color Analysis",
        "description": "Entity color breakdown by layer and type, showing RGB values and AutoCAD color names"
    })
    rows.append({
        "identifier": "Extraction Issues",
        "description": "Unresolved anonymous blocks and other extraction problems requiring attention"
    })
    rows.append({
        "identifier": "Block Definitions",
        "description": "All block definitions in the drawing with insertion status and nesting relationships"
    })
    rows.append({
        "identifier": "Attribute Analysis",
        "description": "Block attribute details showing unique tag/value combinations per block"
    })

    # Create DataFrame with specific column names
    df = pd.DataFrame(rows)
    # Rename columns for display
    df.columns = ["Identifier", "Description"]

    df.to_excel(writer, sheet_name=EXCEL_SHEET_INSTRUCTIONS, index=False)
    logger.info(f"Instructions sheet created with {len(df)} rows")
```

### Step 3: Create Instructions Sheet Formatting Function
- Open `app/core/excel_formatting.py`
- Add `EXCEL_SHEET_INSTRUCTIONS` to the imports from constants (around line 25-35)
- Add the `_format_instructions_sheet` function after the existing formatting functions:

```python
def _format_instructions_sheet(wb: Workbook) -> None:
    """Apply formatting to the Instructions sheet.

    This function applies:
    - Column widths (A: 20, B: 60)
    - Bold font on section headers ("Color Coding" and "Sheet Descriptions")
    - Text wrapping on Column B (descriptions)
    - Color fills on sample cells in the Color Coding section
    - NO auto-filter (static reference content)
    - NO freeze panes (short, static content)

    Args:
        wb: openpyxl Workbook object containing the Instructions sheet
    """
    if EXCEL_SHEET_INSTRUCTIONS not in wb.sheetnames:
        logger.info("Instructions sheet not found, skipping formatting")
        return

    ws = wb[EXCEL_SHEET_INSTRUCTIONS]

    # Set column widths
    ws.column_dimensions["A"].width = 20  # Identifier column
    ws.column_dimensions["B"].width = 60  # Description column

    # Define bold font for section headers
    from openpyxl.styles import Font
    bold_font = Font(bold=True)

    # Define text wrapping alignment for descriptions
    wrap_alignment = Alignment(wrap_text=True, vertical="top")

    # Apply text wrapping to header row
    for cell in ws[1]:
        cell.alignment = wrap_alignment

    # Apply formatting to data rows
    # Row structure:
    # 1: Header (Identifier, Description)
    # 2: "Color Coding" section header
    # 3-6: Color rows (Yellow, Orange, Red, Light Green)
    # 7: Empty separator
    # 8: "Sheet Descriptions" section header
    # 9-18: Sheet description rows

    # Apply bold to section headers (rows 2 and 8)
    section_header_rows = [2, 8]
    for row_idx in section_header_rows:
        cell = ws.cell(row=row_idx, column=1)
        if cell.value in ["Color Coding", "Sheet Descriptions"]:
            cell.font = bold_font

    # Apply text wrapping to description column (B) for all data rows
    for row_idx in range(2, ws.max_row + 1):
        ws.cell(row=row_idx, column=2).alignment = wrap_alignment

    # Apply color fills to color sample cells in Column B
    # Rows 3-6 correspond to Yellow, Orange, Red, Light Green
    color_fills = [
        (3, EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE),   # Yellow
        (4, EXCEL_FILL_COLOR_SCALE_NEGATIVE),            # Orange
        (5, EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE),   # Red
        (6, EXCEL_FILL_COLOR_NESTED_BLOCK),              # Light Green
    ]

    for row_idx, fill_color in color_fills:
        fill = PatternFill(
            start_color=fill_color,
            end_color=fill_color,
            fill_type="solid",
        )
        ws.cell(row=row_idx, column=2).fill = fill

    # NOTE: NO auto-filter applied (static reference content)
    # NOTE: NO freeze panes applied (short, static content)

    logger.info("Instructions sheet formatted with color samples and bold headers")
```

### Step 4: Update write_excel Function - Sheet Creation
- In `app/core/excel_writer.py`, locate the `write_excel()` function (around line 334)
- Find the `with pd.ExcelWriter(full_path, engine="openpyxl") as writer:` block (around line 398)
- Add `_create_instructions_sheet(writer)` as the FIRST sheet creation call, before `_create_all_blocks_sheet`:

```python
        # Create Excel writer
        with pd.ExcelWriter(full_path, engine="openpyxl") as writer:
            # Sheet 0: Instructions (static reference content)
            _create_instructions_sheet(writer)

            # Sheet 1: All Blocks (consolidated block-centric view)
            _create_all_blocks_sheet(extraction_data, writer)
            # ... rest of sheets
```

### Step 5: Update write_excel Function - Sheet Formatting
- In the same `write_excel()` function, locate the formatting section after `wb = load_workbook(full_path)` (around line 431)
- Add `_format_instructions_sheet(wb)` as the FIRST formatting call:

```python
        # Load workbook for post-processing (formatting)
        logger.debug("Loading workbook for formatting stage...")
        wb = load_workbook(full_path)

        # Apply formatting to all sheets
        logger.debug("Applying formatting to Instructions sheet...")
        _format_instructions_sheet(wb)
        logger.debug("Applying formatting to All Blocks sheet...")
        _format_all_blocks_sheet(wb)
        # ... rest of formatting calls
```

### Step 6: Update Imports in excel_writer.py
- Ensure `_format_instructions_sheet` is imported from `excel_formatting` module
- Add to the existing import block around line 102-114:

```python
from .excel_formatting import (
    _format_all_blocks_sheet,
    _format_annotations_analysis_sheet,
    _format_attribute_analysis_sheet,
    _format_block_analysis_sheet,
    _format_block_definitions_sheet,
    _format_block_geometry_analysis_sheet,
    _format_color_analysis_sheet,
    _format_entity_summary_sheet,
    _format_extraction_issues_sheet,
    _format_instructions_sheet,  # ADD THIS
    _format_layer_analysis_sheet,
    format_header,
)
```

### Step 7: Create Writer Unit Tests
- Create new file `app/tests/core/excel_writer/test_excel_writer_instructions.py`
- Add comprehensive tests for the Instructions sheet writer function:

```python
"""
Unit tests for the Instructions sheet creation in excel_writer module.

This test suite validates:
- Instructions sheet is created with correct content
- Instructions sheet appears as the first (leftmost) tab
- Color coding section contains all four colors with descriptions
- Sheet descriptions section contains all 10 sheet descriptions
"""

import os
from pathlib import Path

import pytest
from openpyxl import load_workbook

from core.constants import EXCEL_SHEET_INSTRUCTIONS
from core.excel_writer import write_excel
from core.extractor import ExtractionResult


class TestInstructionsSheetCreation:
    """Test suite for Instructions sheet creation."""

    def test_instructions_sheet_created(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Instructions sheet is created in the workbook."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        # Create dummy input file
        Path(input_file).touch()

        # Generate Excel
        write_excel(sample_extraction_data, input_file, output_file)

        # Verify Instructions sheet exists
        wb = load_workbook(output_file)
        assert EXCEL_SHEET_INSTRUCTIONS in wb.sheetnames

    def test_instructions_sheet_is_first(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Instructions sheet is the first (leftmost) tab."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        assert wb.sheetnames[0] == EXCEL_SHEET_INSTRUCTIONS

    def test_instructions_sheet_color_coding_section(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Color Coding section header exists."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 2 should be "Color Coding" section header
        assert ws.cell(row=2, column=1).value == "Color Coding"

    def test_instructions_sheet_four_colors(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that all four color descriptions are present."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Check color names in Column A (rows 3-6)
        color_names = [
            ws.cell(row=3, column=1).value,
            ws.cell(row=4, column=1).value,
            ws.cell(row=5, column=1).value,
            ws.cell(row=6, column=1).value,
        ]
        assert "Yellow" in color_names
        assert "Orange" in color_names
        assert "Red" in color_names
        assert "Light Green" in color_names

    def test_instructions_sheet_sheet_descriptions_section(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Sheet Descriptions section header exists."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 8 should be "Sheet Descriptions" section header
        assert ws.cell(row=8, column=1).value == "Sheet Descriptions"

    def test_instructions_sheet_ten_sheet_descriptions(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that all 10 sheet descriptions are present."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Sheet names should be in Column A (rows 9-18)
        sheet_names = [ws.cell(row=i, column=1).value for i in range(9, 19)]
        expected_sheets = [
            "All Blocks",
            "Block Analysis",
            "Layer Analysis",
            "Entity Summary",
            "Block Geometry Analysis",
            "Annotations Analysis",
            "Color Analysis",
            "Extraction Issues",
            "Block Definitions",
            "Attribute Analysis",
        ]
        for expected in expected_sheets:
            assert expected in sheet_names, f"Missing sheet description: {expected}"

    def test_instructions_sheet_row_count(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that Instructions sheet has expected number of rows."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Expected rows:
        # 1: Header (Identifier, Description)
        # 2: Color Coding section header
        # 3-6: Four color rows
        # 7: Empty separator
        # 8: Sheet Descriptions section header
        # 9-18: Ten sheet description rows
        # Total: 18 rows
        assert ws.max_row == 18

    def test_instructions_sheet_column_headers(
        self, temp_dir: str, sample_extraction_data: ExtractionResult
    ) -> None:
        """Test that column headers are set correctly."""
        input_file = os.path.join(temp_dir, "test.dxf")
        output_file = os.path.join(temp_dir, "output.xlsx")

        Path(input_file).touch()
        write_excel(sample_extraction_data, input_file, output_file)

        wb = load_workbook(output_file)
        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        assert ws.cell(row=1, column=1).value == "Identifier"
        assert ws.cell(row=1, column=2).value == "Description"
```

### Step 8: Create Formatting Unit Tests
- Create new file `app/tests/core/excel_formatting/test_formatting_instructions.py`
- Add comprehensive tests for the Instructions sheet formatting function:

```python
"""
Unit tests for the Instructions sheet formatting in excel_formatting module.

This test suite validates:
- Column widths are set correctly
- Bold font is applied to section headers
- Text wrapping is enabled on description column
- Color fills are applied to color sample cells
- NO auto-filter is applied
- NO freeze panes are applied
- Empty and missing sheet handling
"""

from typing import cast

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from core.constants import (
    EXCEL_FILL_COLOR_NESTED_BLOCK,
    EXCEL_FILL_COLOR_SCALE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE,
    EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE,
    EXCEL_SHEET_INSTRUCTIONS,
)
from core.excel_formatting import _format_instructions_sheet


class TestInstructionsSheetFormatting:
    """Test suite for _format_instructions_sheet function."""

    def _create_instructions_workbook(self) -> Workbook:
        """Create a workbook with Instructions sheet populated with expected content."""
        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_INSTRUCTIONS

        # Add header row
        ws.append(["Identifier", "Description"])

        # Color Coding section
        ws.append(["Color Coding", ""])
        ws.append(["Yellow", "Scale variance detected"])
        ws.append(["Orange", "Negative scale detected"])
        ws.append(["Red", "Scale variance with negatives"])
        ws.append(["Light Green", "Nested block"])

        # Separator
        ws.append(["", ""])

        # Sheet Descriptions section
        ws.append(["Sheet Descriptions", ""])
        ws.append(["All Blocks", "Consolidated block-centric view"])
        ws.append(["Block Analysis", "Simplified inventory"])

        return wb

    def test_format_instructions_column_widths(self, temp_dir: str) -> None:
        """Test that column widths are set correctly."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]
        assert ws.column_dimensions["A"].width == 20
        assert ws.column_dimensions["B"].width == 60

    def test_format_instructions_bold_section_headers(self, temp_dir: str) -> None:
        """Test that section headers have bold font."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 2: "Color Coding" should be bold
        color_coding_cell = ws.cell(row=2, column=1)
        assert color_coding_cell.font.bold is True

        # Row 8: "Sheet Descriptions" should be bold
        sheet_desc_cell = ws.cell(row=8, column=1)
        assert sheet_desc_cell.font.bold is True

    def test_format_instructions_text_wrapping(self, temp_dir: str) -> None:
        """Test that description column has text wrapping."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Check text wrapping on description cells
        for row_idx in range(2, ws.max_row + 1):
            desc_cell = ws.cell(row=row_idx, column=2)
            assert desc_cell.alignment is not None
            assert desc_cell.alignment.wrap_text is True

    def test_format_instructions_no_autofilter(self, temp_dir: str) -> None:
        """Test that NO auto-filter is applied to Instructions sheet."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # auto_filter.ref should be None or empty
        assert ws.auto_filter.ref is None or ws.auto_filter.ref == ""

    def test_format_instructions_no_freeze_panes(self, temp_dir: str) -> None:
        """Test that NO freeze panes are applied to Instructions sheet."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # freeze_panes should be None
        assert ws.freeze_panes is None

    def test_format_instructions_yellow_fill(self, temp_dir: str) -> None:
        """Test that Yellow row has correct color fill."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 3 (Yellow) should have yellow fill in column B
        yellow_cell = ws.cell(row=3, column=2)
        assert yellow_cell.fill is not None
        assert yellow_cell.fill.fill_type == "solid"
        assert yellow_cell.fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE

    def test_format_instructions_orange_fill(self, temp_dir: str) -> None:
        """Test that Orange row has correct color fill."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 4 (Orange) should have orange fill in column B
        orange_cell = ws.cell(row=4, column=2)
        assert orange_cell.fill is not None
        assert orange_cell.fill.fill_type == "solid"
        assert orange_cell.fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_NEGATIVE

    def test_format_instructions_red_fill(self, temp_dir: str) -> None:
        """Test that Red row has correct color fill."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 5 (Red) should have red fill in column B
        red_cell = ws.cell(row=5, column=2)
        assert red_cell.fill is not None
        assert red_cell.fill.fill_type == "solid"
        assert red_cell.fill.start_color.rgb == EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE

    def test_format_instructions_green_fill(self, temp_dir: str) -> None:
        """Test that Light Green row has correct color fill."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        # Row 6 (Light Green) should have green fill in column B
        green_cell = ws.cell(row=6, column=2)
        assert green_cell.fill is not None
        assert green_cell.fill.fill_type == "solid"
        assert green_cell.fill.start_color.rgb == EXCEL_FILL_COLOR_NESTED_BLOCK

    def test_format_instructions_all_color_fills(self, temp_dir: str) -> None:
        """Test that all four color fills are applied correctly."""
        wb = self._create_instructions_workbook()
        _format_instructions_sheet(wb)

        ws = wb[EXCEL_SHEET_INSTRUCTIONS]

        expected_fills = [
            (3, EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE),   # Yellow
            (4, EXCEL_FILL_COLOR_SCALE_NEGATIVE),            # Orange
            (5, EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE),   # Red
            (6, EXCEL_FILL_COLOR_NESTED_BLOCK),              # Light Green
        ]

        for row_idx, expected_color in expected_fills:
            cell = ws.cell(row=row_idx, column=2)
            assert cell.fill is not None
            assert cell.fill.fill_type == "solid"
            assert cell.fill.start_color.rgb == expected_color

    def test_format_instructions_empty_sheet(self, temp_dir: str) -> None:
        """Test that empty Instructions sheet is handled gracefully."""
        wb = Workbook()
        ws = cast(Worksheet, wb.active)
        ws.title = EXCEL_SHEET_INSTRUCTIONS

        # Apply formatting (should not crash on empty sheet)
        _format_instructions_sheet(wb)

        # Column widths should still be set
        assert ws.column_dimensions["A"].width == 20
        assert ws.column_dimensions["B"].width == 60

    def test_format_instructions_missing_sheet(self, temp_dir: str) -> None:
        """Test that missing Instructions sheet is handled gracefully."""
        wb = Workbook()
        # Default sheet has different name, so Instructions doesn't exist

        # Should not raise an exception
        _format_instructions_sheet(wb)

        # Verify default sheet is unchanged
        assert len(wb.sheetnames) == 1
        assert EXCEL_SHEET_INSTRUCTIONS not in wb.sheetnames
```

### Step 9: Run Validation Commands
Execute all validation commands to ensure implementation is correct with zero regressions:

- Run Instructions sheet writer tests
- Run Instructions sheet formatting tests
- Run all excel_writer tests
- Run all excel_formatting tests
- Run full test suite
- Run type checker
- Run linter

## Testing Strategy

### Unit Tests

**Writer Tests (`test_excel_writer_instructions.py`):**
- Test Instructions sheet is created in workbook
- Test Instructions sheet is first (leftmost) tab
- Test Color Coding section header exists
- Test all four color descriptions are present
- Test Sheet Descriptions section header exists
- Test all 10 sheet descriptions are present
- Test correct row count (18 rows)
- Test column headers ("Identifier", "Description")

**Formatting Tests (`test_formatting_instructions.py`):**
- Test column widths (A=20, B=60)
- Test bold font on section headers
- Test text wrapping on description column
- Test NO auto-filter applied
- Test NO freeze panes applied
- Test color fills for all four colors
- Test empty sheet handling
- Test missing sheet handling

### Integration Tests
- Test `write_excel()` produces workbook with Instructions sheet as first tab
- Test Instructions sheet contains correct static content after full Excel generation

### Edge Cases
- Empty extraction data: Instructions sheet should still be created
- Missing sheet: `_format_instructions_sheet()` should log and skip gracefully
- Empty Instructions sheet: Formatting should apply column widths without crash

### Playwright MCP Tests
Not applicable - this is an Excel output feature, not a UI feature.

## Acceptance Criteria
- [ ] `EXCEL_SHEET_INSTRUCTIONS` constant added to `constants.py`
- [ ] `_create_instructions_sheet()` function creates sheet with correct content
- [ ] `_format_instructions_sheet()` function applies correct formatting
- [ ] Instructions sheet appears as first (leftmost) tab when opening Excel file
- [ ] Color Coding section displays all four colors (Yellow, Orange, Red, Light Green) with correct meanings
- [ ] Color sample cells in Column B display actual fill colors
- [ ] Sheet Descriptions section lists all 10 sheets with accurate descriptions
- [ ] Column A has width 20, Column B has width 60
- [ ] Section headers ("Color Coding", "Sheet Descriptions") are bold
- [ ] Column B (descriptions) has text wrapping enabled
- [ ] No auto-filter is applied to the Instructions sheet
- [ ] No freeze panes are applied to the Instructions sheet
- [ ] All existing tests pass (no regressions)
- [ ] Type checking passes
- [ ] Linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run pytest app/tests/core/excel_writer/test_excel_writer_instructions.py -v` - Run new Instructions sheet writer tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_instructions.py -v` - Run new Instructions sheet formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all excel_writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all excel_formatting tests
- `uv run pytest app/tests/ -v` - Run full test suite
- `uv run mypy app/` - Type check
- `uv run ruff check app/` - Lint check

## Notes

- **Sheet Position:** Creating the Instructions sheet FIRST in the `pd.ExcelWriter` context ensures it appears as the leftmost tab. Pandas preserves sheet creation order, so no explicit `move_sheet()` call is needed.

- **No Auto-Filter/Freeze Panes:** Unlike other sheets that contain filterable data, the Instructions sheet is static reference content. Auto-filter and freeze panes are intentionally omitted to keep the formatting simple and appropriate for the content type.

- **Color Constants:** The four highlight colors are already defined in `constants.py`:
  - `EXCEL_FILL_COLOR_SCALE_VARIANCE_POSITIVE` (Yellow: `FFFFFF00`)
  - `EXCEL_FILL_COLOR_SCALE_NEGATIVE` (Orange: `FFA500FF`)
  - `EXCEL_FILL_COLOR_SCALE_VARIANCE_NEGATIVE` (Red: `FFFF0000`)
  - `EXCEL_FILL_COLOR_NESTED_BLOCK` (Light Green: `FF90EE90`)

- **Row Structure:** The Instructions sheet has a fixed structure (18 rows total):
  - Row 1: Column headers
  - Row 2: "Color Coding" section header
  - Rows 3-6: Four color descriptions
  - Row 7: Empty separator
  - Row 8: "Sheet Descriptions" section header
  - Rows 9-18: Ten sheet descriptions

- **Future Considerations:** If new sheets are added to the Excel output, remember to update the Sheet Descriptions section in `_create_instructions_sheet()` to include them.
