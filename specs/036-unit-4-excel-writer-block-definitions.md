# Feature: Nested Block Detection - Unit 4: Excel Writer Block Definitions Sheet

## Feature Description
This unit implements the Excel writer and formatting functions for the new "Block Definitions" sheet. It adds `_create_block_definitions_sheet()` to `excel_writer.py` and `_format_block_definitions_sheet()` to `excel_formatting.py`, then integrates these functions into the main writer and formatter pipelines. The Block Definitions sheet displays all block definitions from the DXF file with their insertion status, nesting information, and entity counts, providing users with a comprehensive overview of the block hierarchy.

## User Story
As a CAD data analyst
I want to see a complete list of all block definitions in an Excel sheet
So that I can understand which blocks are inserted, nested, unused, or system blocks without manually inspecting the DXF file

## Problem Statement
After Unit 3, the extractor now returns `all_block_definitions` containing complete metadata for every block definition in the DXF file. However, this data is not yet exposed to users in the Excel output. Users need a dedicated sheet that:
1. Lists all block definitions with their raw and resolved names
2. Shows insertion status (Inserted, Nested Only, Unused, System, etc.)
3. Indicates which blocks are nested and their parent block names
4. Displays entity counts for each block definition
5. Highlights nested blocks visually for quick identification

## Solution Statement
Implement two new functions to create and format the Block Definitions sheet:
1. `_create_block_definitions_sheet()` in `excel_writer.py` - Creates the sheet with sorted data from `all_block_definitions`
2. `_format_block_definitions_sheet()` in `excel_formatting.py` - Applies formatting including green highlighting for nested blocks
3. Integrate both functions into the existing `write_excel()` and formatting pipeline
4. Add a new fill color constant for nested block highlighting

## Relevant Files
Use these files to implement the feature:

- **app/core/excel_writer.py** - Main Excel generation module; will add `_create_block_definitions_sheet()` function and integrate it into `write_excel()`
- **app/core/excel_formatting.py** - Excel formatting utilities; will add `_format_block_definitions_sheet()` function and export it
- **app/core/constants.py** - Contains Excel constants; already has `EXCEL_SHEET_BLOCK_DEFINITIONS` and column constants from Unit 1-2; will add new fill color constant
- **app/core/types.py** - Contains `BlockDefinitionRecord` TypedDict (reference only, no changes needed)
- **app/core/extractor.py** - Contains `ExtractionResult` TypedDict with `all_block_definitions` field (reference only, no changes needed)
- **app/tests/core/excel_writer/conftest.py** - Shared fixtures; will update `sample_extraction_data` to include block definitions
- **app/tests/core/excel_formatting/conftest.py** - Shared fixtures for formatting tests

### New Files
- **app/tests/core/excel_writer/test_excel_writer_block_definitions.py** - New test file for Block Definitions sheet creation tests
- **app/tests/core/excel_formatting/test_formatting_block_definitions.py** - New test file for Block Definitions sheet formatting tests

## Implementation Plan
### Phase 1: Foundation
Add the green fill color constant for nested block highlighting to `constants.py`.

### Phase 2: Core Implementation
1. Add `_create_block_definitions_sheet()` function to `excel_writer.py` with:
   - Data extraction from `all_block_definitions`
   - Row building with proper column mapping
   - Sorting by insertion status priority, then by resolved name
   - DataFrame creation and export to Excel
2. Add `_format_block_definitions_sheet()` function to `excel_formatting.py` with:
   - Auto-filter application
   - Frozen header row
   - Column width settings
   - Header text wrapping
   - Green fill highlighting for nested blocks (True in is_nested column)

### Phase 3: Integration
1. Update `write_excel()` to call `_create_block_definitions_sheet()`
2. Update the formatting section to call `_format_block_definitions_sheet()`
3. Update imports in both files
4. Update test fixtures to include block definitions data
5. Create comprehensive test suites for both functions

## Step by Step Tasks

### Step 1: Add Fill Color Constant
- Open `app/core/constants.py`
- Add new constant after the existing fill color constants (around line 136):
  ```python
  # Green: Highlight color for nested blocks in Block Definitions sheet
  EXCEL_FILL_COLOR_NESTED_BLOCK: str = "FF90EE90"
  ```
- This light green color (LightGreen) provides good visibility while being distinct from existing colors

### Step 2: Add Column Constant Imports to excel_writer.py
- Open `app/core/excel_writer.py`
- Add imports for the Block Definitions constants to the existing imports from `.constants`:
  ```python
  EXCEL_COLUMN_BLOCK_IS_NESTED,
  EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
  EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
  EXCEL_COLUMN_BLOCK_RAW_NAME,
  EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
  EXCEL_SHEET_BLOCK_DEFINITIONS,
  ```
- Note: `EXCEL_COLUMN_BLOCK_ENTITY_COUNT` is already imported

### Step 3: Add _create_block_definitions_sheet() Function
- In `app/core/excel_writer.py`, add the new function after `_create_extraction_issues_sheet()` (around line 894):
  ```python
  def _create_block_definitions_sheet(
      data: ExtractionResult, writer: pd.ExcelWriter
  ) -> None:
      """Create the Block Definitions sheet with all block definitions and nesting status."""
      logger.info("Creating Block Definitions sheet...")

      all_block_definitions = data.get("all_block_definitions", {})

      if not all_block_definitions:
          logger.info("No block definitions found, skipping Block Definitions sheet")
          return

      # Build DataFrame rows
      rows = []
      for raw_name, record in all_block_definitions.items():
          parent_names_str = ", ".join(record["block_nested_parent_names"])

          rows.append({
              EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
              EXCEL_COLUMN_BLOCK_RESOLVED_NAME: record["block_resolved_name"],
              EXCEL_COLUMN_BLOCK_INSERTION_STATUS: record["block_insertion_status"],
              EXCEL_COLUMN_BLOCK_IS_NESTED: record["block_is_nested"],
              EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: parent_names_str,
              EXCEL_COLUMN_BLOCK_ENTITY_COUNT: record["block_entity_count"],
          })

      # Sort by insertion status (Inserted first, System last), then by resolved name
      status_order = {
          "Inserted": 0,
          "Nested Only": 1,
          "Unused": 2,
          "Unresolved (*U)": 3,
          "Unresolved (A$C)": 4,
          "System": 5,
          "System (Dimension)": 6,
          "System (Hatch)": 7,
      }
      rows.sort(key=lambda r: (
          status_order.get(r[EXCEL_COLUMN_BLOCK_INSERTION_STATUS], 99),
          r[EXCEL_COLUMN_BLOCK_RESOLVED_NAME].lower(),
      ))

      df = pd.DataFrame(rows)

      # Format column headers for Excel display
      df.columns = [format_header(col) for col in df.columns]

      df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS, index=False)
      logger.info(f"Block Definitions sheet created with {len(df)} rows")
  ```

### Step 4: Update write_excel() to Call New Sheet Function
- In `app/core/excel_writer.py`, locate the `write_excel()` function
- Add a new sheet creation call after the Extraction Issues sheet (around line 348):
  ```python
  # Sheet 8: Block Definitions
  _create_block_definitions_sheet(extraction_data, writer)
  ```

### Step 5: Add Import for _format_block_definitions_sheet
- In `app/core/excel_writer.py`, add the import for the new formatting function:
  ```python
  from .excel_formatting import (
      _format_annotations_analysis_sheet,
      _format_block_analysis_sheet,
      _format_block_definitions_sheet,  # Add this line
      _format_block_geometry_analysis_sheet,
      ...
  )
  ```

### Step 6: Update write_excel() to Call New Formatting Function
- In `app/core/excel_writer.py`, add the formatting call after the Extraction Issues formatting (around line 368):
  ```python
  logger.debug("Applying formatting to Block Definitions sheet...")
  _format_block_definitions_sheet(wb)
  ```

### Step 7: Add Imports to excel_formatting.py
- Open `app/core/excel_formatting.py`
- Add imports for the new constants:
  ```python
  from .constants import (
      EXCEL_FILL_COLOR_EXTRACTION_ISSUE,
      EXCEL_FILL_COLOR_NESTED_BLOCK,  # Add this line
      EXCEL_FILL_COLOR_SCALE_NEGATIVE,
      ...
      EXCEL_SHEET_BLOCK_DEFINITIONS,  # Add this line
      EXCEL_SHEET_BLOCK_ANALYSIS,
      ...
  )
  ```

### Step 8: Add _format_block_definitions_sheet() Function
- In `app/core/excel_formatting.py`, add the new function after `_format_extraction_issues_sheet()` (at the end of the file):
  ```python
  def _format_block_definitions_sheet(wb: Workbook) -> None:
      """Apply formatting to the Block Definitions sheet with green highlighting for nested blocks."""
      if EXCEL_SHEET_BLOCK_DEFINITIONS not in wb.sheetnames:
          logger.info("Block Definitions sheet not found, skipping formatting")
          return

      ws = wb[EXCEL_SHEET_BLOCK_DEFINITIONS]

      # Apply auto-filter
      if ws.dimensions:
          ws.auto_filter.ref = ws.dimensions

      # Freeze header row
      ws.freeze_panes = "A2"
      logger.info("Frozen panes applied to Block Definitions sheet")

      # Set column widths (6 columns: A-F)
      ws.column_dimensions["A"].width = 30  # block_raw_name
      ws.column_dimensions["B"].width = 30  # block_resolved_name
      ws.column_dimensions["C"].width = 20  # block_insertion_status
      ws.column_dimensions["D"].width = 15  # block_is_nested
      ws.column_dimensions["E"].width = 40  # block_nested_parent_names
      ws.column_dimensions["F"].width = 20  # block_entity_count

      # Enable text wrapping on header row
      header_alignment = Alignment(wrap_text=True, vertical="top")
      for cell in ws[1]:
          cell.alignment = header_alignment

      # Define green fill for nested blocks
      green_fill = PatternFill(
          start_color=EXCEL_FILL_COLOR_NESTED_BLOCK,
          end_color=EXCEL_FILL_COLOR_NESTED_BLOCK,
          fill_type="solid",
      )

      # Apply green highlighting to rows where block_is_nested is True
      # Column D contains the is_nested boolean
      rows_highlighted = 0
      for row_idx in range(2, ws.max_row + 1):
          is_nested_value = ws.cell(row=row_idx, column=4).value
          if is_nested_value is True or is_nested_value == "True" or is_nested_value == True:
              # Apply fill to entire row (columns A-F)
              for col_idx in range(1, 7):
                  ws.cell(row=row_idx, column=col_idx).fill = green_fill
              rows_highlighted += 1

      # Apply right-alignment to entity_count column (F)
      right_alignment = Alignment(horizontal="right")
      for row_idx in range(2, ws.max_row + 1):
          ws.cell(row=row_idx, column=6).alignment = right_alignment

      logger.info(
          f"Block Definitions sheet formatted with {rows_highlighted} nested block rows highlighted"
      )
  ```

### Step 9: Update Test Fixture with Block Definitions Data
- Open `app/tests/core/excel_writer/conftest.py`
- Update the `sample_extraction_data` fixture to include realistic block definitions:
  ```python
  "all_block_definitions": {
      "VALVE": {
          "block_raw_name": "VALVE",
          "block_resolved_name": "VALVE",
          "block_insertion_status": "Inserted",
          "block_is_nested": False,
          "block_nested_parent_names": [],
          "block_entity_count": 8,
      },
      "PIPE": {
          "block_raw_name": "PIPE",
          "block_resolved_name": "PIPE",
          "block_insertion_status": "Inserted",
          "block_is_nested": True,
          "block_nested_parent_names": ["VALVE"],
          "block_entity_count": 12,
      },
      "TAG": {
          "block_raw_name": "TAG",
          "block_resolved_name": "TAG",
          "block_insertion_status": "Nested Only",
          "block_is_nested": True,
          "block_nested_parent_names": ["VALVE", "PIPE"],
          "block_entity_count": 4,
      },
      "*Model_Space": {
          "block_raw_name": "*Model_Space",
          "block_resolved_name": "*Model_Space",
          "block_insertion_status": "System",
          "block_is_nested": False,
          "block_nested_parent_names": [],
          "block_entity_count": 50,
      },
  },
  "nested_block_parents": {
      "PIPE": ["VALVE"],
      "TAG": ["PIPE", "VALVE"],
  },
  ```
- Also update all other fixtures (`annotation_extraction_data`, `color_analysis_data`, `extraction_issues_data`, `no_issues_data`) to include the same block definitions for consistency

### Step 10: Create Test File for Block Definitions Sheet Creation
- Create new file `app/tests/core/excel_writer/test_excel_writer_block_definitions.py`:
  ```python
  """
  Unit tests for the excel_writer module - Block Definitions sheet.

  This test suite validates the Block Definitions sheet generation including:
  - Sheet creation with correct columns
  - Sorting by insertion status and resolved name
  - Data population from all_block_definitions
  - Empty data handling
  - Integration with main write_excel function
  """

  import os
  from pathlib import Path

  import pandas as pd
  import pytest
  from openpyxl import load_workbook

  from core.constants import (
      EXCEL_COLUMN_BLOCK_ENTITY_COUNT,
      EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
      EXCEL_COLUMN_BLOCK_IS_NESTED,
      EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
      EXCEL_COLUMN_BLOCK_RAW_NAME,
      EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
      EXCEL_SHEET_BLOCK_DEFINITIONS,
  )
  from core.excel_formatting import format_header
  from core.excel_writer import write_excel
  from core.extractor import ExtractionResult


  class TestBlockDefinitionsSheet:
      """Test suite for Block Definitions sheet creation."""

      # Add tests here following patterns from test_excel_writer_core.py
  ```

### Step 11: Add Block Definitions Sheet Tests - Existence and Structure
- Add tests to verify the sheet exists and has correct columns:
  ```python
  def test_block_definitions_sheet_exists(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that Block Definitions sheet is created when data exists."""
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      wb = load_workbook(excel_path)
      assert EXCEL_SHEET_BLOCK_DEFINITIONS in wb.sheetnames

  def test_block_definitions_sheet_columns(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that Block Definitions sheet has correct 6 columns."""
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

      expected_columns = [
          format_header(EXCEL_COLUMN_BLOCK_RAW_NAME),
          format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME),
          format_header(EXCEL_COLUMN_BLOCK_INSERTION_STATUS),
          format_header(EXCEL_COLUMN_BLOCK_IS_NESTED),
          format_header(EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES),
          format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT),
      ]
      assert list(df.columns) == expected_columns
  ```

### Step 12: Add Block Definitions Sheet Tests - Sorting
- Add tests to verify correct sorting order:
  ```python
  def test_block_definitions_sorted_by_status_then_name(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that Block Definitions are sorted by status priority, then by resolved name."""
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

      # Inserted blocks should come before Nested Only, which comes before System
      statuses = df[format_header(EXCEL_COLUMN_BLOCK_INSERTION_STATUS)].tolist()

      # Find indices for each status
      inserted_indices = [i for i, s in enumerate(statuses) if s == "Inserted"]
      nested_only_indices = [i for i, s in enumerate(statuses) if s == "Nested Only"]
      system_indices = [i for i, s in enumerate(statuses) if s == "System"]

      # All Inserted should come before Nested Only
      if inserted_indices and nested_only_indices:
          assert max(inserted_indices) < min(nested_only_indices)

      # All Nested Only should come before System
      if nested_only_indices and system_indices:
          assert max(nested_only_indices) < min(system_indices)
  ```

### Step 13: Add Block Definitions Sheet Tests - Data Population
- Add tests to verify data is correctly populated:
  ```python
  def test_block_definitions_data_populated(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that block definition data is correctly populated."""
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

      # Find VALVE row
      valve_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_RAW_NAME)] == "VALVE"]
      assert len(valve_rows) == 1
      valve_row = valve_rows.iloc[0]

      assert valve_row[format_header(EXCEL_COLUMN_BLOCK_RESOLVED_NAME)] == "VALVE"
      assert valve_row[format_header(EXCEL_COLUMN_BLOCK_INSERTION_STATUS)] == "Inserted"
      assert valve_row[format_header(EXCEL_COLUMN_BLOCK_IS_NESTED)] == False
      assert valve_row[format_header(EXCEL_COLUMN_BLOCK_ENTITY_COUNT)] == 8

  def test_block_definitions_parent_names_formatted(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that parent names are comma-separated strings."""
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      df = pd.read_excel(excel_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

      # Find TAG row which has multiple parents
      tag_rows = df[df[format_header(EXCEL_COLUMN_BLOCK_RAW_NAME)] == "TAG"]
      assert len(tag_rows) == 1
      tag_row = tag_rows.iloc[0]

      parent_names = tag_row[format_header(EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES)]
      assert "PIPE" in parent_names
      assert "VALVE" in parent_names
      assert "," in parent_names
  ```

### Step 14: Add Block Definitions Sheet Tests - Empty Data Handling
- Add tests for empty data scenarios:
  ```python
  def test_block_definitions_empty_data_no_sheet(self, temp_dir: str) -> None:
      """Test that empty all_block_definitions does not create the sheet."""
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
      }
      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(empty_data, output_path)

      wb = load_workbook(excel_path)
      assert EXCEL_SHEET_BLOCK_DEFINITIONS not in wb.sheetnames
  ```

### Step 15: Create Test File for Block Definitions Sheet Formatting
- Create new file `app/tests/core/excel_formatting/test_formatting_block_definitions.py`:
  ```python
  """
  Unit tests for the excel_formatting module - Block Definitions sheet.

  This test suite validates Block Definitions sheet formatting including:
  - Auto-filter application
  - Column width settings
  - Frozen panes
  - Green highlighting for nested blocks
  """

  from typing import cast

  from openpyxl import Workbook
  from openpyxl.worksheet.worksheet import Worksheet

  from core.constants import (
      EXCEL_FILL_COLOR_NESTED_BLOCK,
      EXCEL_SHEET_BLOCK_DEFINITIONS,
  )
  from core.excel_formatting import _format_block_definitions_sheet


  class TestBlockDefinitionsFormatting:
      """Test suite for _format_block_definitions_sheet function."""

      # Add tests here
  ```

### Step 16: Add Block Definitions Formatting Tests - Auto-filter and Column Widths
- Add formatting tests:
  ```python
  def test_format_block_definitions_autofilter(self, temp_dir: str) -> None:
      """Test that auto-filter is applied to Block Definitions sheet."""
      wb = Workbook()
      ws = cast(Worksheet, wb.active)
      ws.title = EXCEL_SHEET_BLOCK_DEFINITIONS

      ws.append(["block_raw_name", "block_resolved_name", "block_insertion_status",
                 "block_is_nested", "block_nested_parent_names", "block_entity_count"])
      ws.append(["VALVE", "VALVE", "Inserted", False, "", 8])

      _format_block_definitions_sheet(wb)

      assert ws.auto_filter.ref is not None
      assert ws.auto_filter.ref == "A1:F2"

  def test_format_block_definitions_column_widths(self, temp_dir: str) -> None:
      """Test that column widths are set correctly."""
      wb = Workbook()
      ws = cast(Worksheet, wb.active)
      ws.title = EXCEL_SHEET_BLOCK_DEFINITIONS

      ws.append(["block_raw_name", "block_resolved_name", "block_insertion_status",
                 "block_is_nested", "block_nested_parent_names", "block_entity_count"])

      _format_block_definitions_sheet(wb)

      assert ws.column_dimensions["A"].width == 30  # block_raw_name
      assert ws.column_dimensions["B"].width == 30  # block_resolved_name
      assert ws.column_dimensions["C"].width == 20  # block_insertion_status
      assert ws.column_dimensions["D"].width == 15  # block_is_nested
      assert ws.column_dimensions["E"].width == 40  # block_nested_parent_names
      assert ws.column_dimensions["F"].width == 20  # block_entity_count

  def test_format_block_definitions_frozen_panes(self, temp_dir: str) -> None:
      """Test that frozen panes are applied at A2."""
      wb = Workbook()
      ws = cast(Worksheet, wb.active)
      ws.title = EXCEL_SHEET_BLOCK_DEFINITIONS

      ws.append(["block_raw_name", "block_resolved_name", "block_insertion_status",
                 "block_is_nested", "block_nested_parent_names", "block_entity_count"])

      _format_block_definitions_sheet(wb)

      assert ws.freeze_panes == "A2"
  ```

### Step 17: Add Block Definitions Formatting Tests - Green Highlighting
- Add tests for nested block highlighting:
  ```python
  def test_format_block_definitions_green_highlighting_nested(self, temp_dir: str) -> None:
      """Test that nested blocks are highlighted in green."""
      wb = Workbook()
      ws = cast(Worksheet, wb.active)
      ws.title = EXCEL_SHEET_BLOCK_DEFINITIONS

      ws.append(["block_raw_name", "block_resolved_name", "block_insertion_status",
                 "block_is_nested", "block_nested_parent_names", "block_entity_count"])
      ws.append(["VALVE", "VALVE", "Inserted", False, "", 8])
      ws.append(["PIPE", "PIPE", "Inserted", True, "VALVE", 12])
      ws.append(["TAG", "TAG", "Nested Only", True, "VALVE, PIPE", 4])

      _format_block_definitions_sheet(wb)

      # Row 2 (VALVE) should NOT have green fill (not nested)
      assert ws.cell(row=2, column=1).fill.start_color.rgb != EXCEL_FILL_COLOR_NESTED_BLOCK

      # Row 3 (PIPE) should have green fill (nested)
      assert ws.cell(row=3, column=1).fill.start_color.rgb == EXCEL_FILL_COLOR_NESTED_BLOCK
      assert ws.cell(row=3, column=1).fill.fill_type == "solid"

      # Row 4 (TAG) should have green fill (nested)
      assert ws.cell(row=4, column=1).fill.start_color.rgb == EXCEL_FILL_COLOR_NESTED_BLOCK

  def test_format_block_definitions_no_highlighting_non_nested(self, temp_dir: str) -> None:
      """Test that non-nested blocks are not highlighted."""
      wb = Workbook()
      ws = cast(Worksheet, wb.active)
      ws.title = EXCEL_SHEET_BLOCK_DEFINITIONS

      ws.append(["block_raw_name", "block_resolved_name", "block_insertion_status",
                 "block_is_nested", "block_nested_parent_names", "block_entity_count"])
      ws.append(["VALVE", "VALVE", "Inserted", False, "", 8])
      ws.append(["PUMP", "PUMP", "Unused", False, "", 5])

      _format_block_definitions_sheet(wb)

      # Neither row should have green fill
      for row_idx in [2, 3]:
          cell_fill = ws.cell(row=row_idx, column=1).fill
          if cell_fill.fill_type == "solid":
              assert cell_fill.start_color.rgb != EXCEL_FILL_COLOR_NESTED_BLOCK

  def test_format_block_definitions_missing_sheet_handled(self, temp_dir: str) -> None:
      """Test that missing Block Definitions sheet is handled gracefully."""
      wb = Workbook()
      # Sheet with different name
      ws = cast(Worksheet, wb.active)
      ws.title = "Other Sheet"

      # Should not raise an exception
      _format_block_definitions_sheet(wb)
  ```

### Step 18: Add Integration Test for Eight Sheets
- Update existing test in `test_excel_writer_core.py` to verify 8 sheets:
  ```python
  def test_write_excel_eight_sheets(
      self, temp_dir: str, sample_extraction_data: ExtractionResult
  ) -> None:
      """Test that eight sheets are created with correct names."""
      from core.constants import (
          EXCEL_SHEET_BLOCK_DEFINITIONS,
          EXCEL_SHEET_COLOR_ANALYSIS,
          EXCEL_SHEET_EXTRACTION_ISSUES,
      )

      output_path = os.path.join(temp_dir, "test_drawing.dxf")
      excel_path = write_excel(sample_extraction_data, output_path)

      wb = load_workbook(excel_path)
      assert EXCEL_SHEET_BLOCK_ANALYSIS in wb.sheetnames
      assert EXCEL_SHEET_LAYER_ANALYSIS in wb.sheetnames
      assert EXCEL_SHEET_ENTITY_SUMMARY in wb.sheetnames
      assert EXCEL_SHEET_BLOCK_GEOMETRY_ANALYSIS in wb.sheetnames
      assert EXCEL_SHEET_ANNOTATIONS_ANALYSIS in wb.sheetnames
      assert EXCEL_SHEET_COLOR_ANALYSIS in wb.sheetnames
      assert EXCEL_SHEET_EXTRACTION_ISSUES in wb.sheetnames
      assert EXCEL_SHEET_BLOCK_DEFINITIONS in wb.sheetnames
      assert len(wb.sheetnames) == 8
  ```

### Step 19: Run Validation Commands
- Run type checking with mypy
- Run all excel_writer tests
- Run all excel_formatting tests
- Run full test suite to ensure no regressions

## Testing Strategy
### Unit Tests
Create comprehensive tests in two new test files:

**test_excel_writer_block_definitions.py:**
- `test_block_definitions_sheet_exists` - Verify sheet is created when data exists
- `test_block_definitions_sheet_columns` - Verify correct 6 columns
- `test_block_definitions_sorted_by_status_then_name` - Verify sorting order
- `test_block_definitions_data_populated` - Verify data values
- `test_block_definitions_parent_names_formatted` - Verify comma-separated parent names
- `test_block_definitions_empty_data_no_sheet` - Verify no sheet for empty data
- `test_block_definitions_row_count` - Verify correct number of rows

**test_formatting_block_definitions.py:**
- `test_format_block_definitions_autofilter` - Verify auto-filter
- `test_format_block_definitions_column_widths` - Verify column widths
- `test_format_block_definitions_frozen_panes` - Verify frozen header row
- `test_format_block_definitions_green_highlighting_nested` - Verify green fill for nested
- `test_format_block_definitions_no_highlighting_non_nested` - Verify no fill for non-nested
- `test_format_block_definitions_missing_sheet_handled` - Verify graceful handling

### Integration Tests
- Update `test_write_excel_seven_sheets` to `test_write_excel_eight_sheets`
- Test with real extraction data from `nested_block_test.dxf`
- Verify end-to-end flow from extraction to Excel output

### Edge Cases
- Empty `all_block_definitions` dictionary (no sheet created)
- Blocks with empty parent names list
- Blocks with multiple parent names
- All blocks being system blocks
- Mixed insertion status values
- Boolean values as strings vs actual booleans in is_nested column

### Playwright MCP Tests
- Not applicable for this unit (backend Excel generation only)

## Acceptance Criteria
1. `EXCEL_FILL_COLOR_NESTED_BLOCK` constant is defined in `constants.py`
2. `_create_block_definitions_sheet()` function is implemented in `excel_writer.py`
3. `_format_block_definitions_sheet()` function is implemented in `excel_formatting.py`
4. Block Definitions sheet is created with 6 columns when `all_block_definitions` is not empty
5. Sheet is sorted by insertion status priority (Inserted -> Nested Only -> Unused -> Unresolved -> System), then by resolved name
6. Parent names are displayed as comma-separated strings
7. Nested blocks (is_nested=True) are highlighted with green fill
8. Auto-filter, frozen panes, and column widths are applied correctly
9. Empty `all_block_definitions` does not create the sheet
10. All test fixtures include `all_block_definitions` data
11. `uv run mypy app/` passes with no errors
12. `uv run pytest app/tests/core/excel_writer/test_excel_writer_block_definitions.py -v` passes
13. `uv run pytest app/tests/core/excel_formatting/test_formatting_block_definitions.py -v` passes
14. `uv run pytest app/tests/` passes with no failures

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `uv run mypy app/` - Run type checking to verify types are valid
- `uv run pytest app/tests/core/excel_writer/test_excel_writer_block_definitions.py -v` - Run Block Definitions sheet creation tests
- `uv run pytest app/tests/core/excel_formatting/test_formatting_block_definitions.py -v` - Run Block Definitions sheet formatting tests
- `uv run pytest app/tests/core/excel_writer/ -v` - Run all Excel writer tests
- `uv run pytest app/tests/core/excel_formatting/ -v` - Run all Excel formatting tests
- `uv run pytest app/tests/ -v` - Run full test suite for regression testing
- `uv run python -c "from core.extractor import extract_blocks; from core.excel_writer import write_excel; r = extract_blocks('app/tests/assets/nested_block_test.dxf'); p = write_excel(r, 'app/tests/assets/nested_block_test.dxf'); print(f'Excel created at: {p}')"` - Verify end-to-end extraction and Excel generation

## Notes
- The `all_block_definitions` field was added to `ExtractionResult` in Unit 3 and is already populated by the extractor
- `EXCEL_COLUMN_BLOCK_ENTITY_COUNT` already exists in `constants.py` (line 30) and is already imported in `excel_writer.py`
- The `format_header()` function automatically converts snake_case column names to Title Case for Excel display
- The green fill color `FF90EE90` is LightGreen, providing good visibility while being distinct from:
  - Yellow (`FFFFFF00`) - used for scale variance
  - Orange (`FFA500FF`) - used for negative scales
  - Red (`FFFF0000`) - used for scale variance with negatives
- Sheet creation is skipped entirely when `all_block_definitions` is empty, rather than creating an empty sheet
- The formatting function handles the case where the sheet doesn't exist (e.g., when skipped due to empty data)
- This unit completes the Excel writer portion of the Nested Block Detection feature; the feature is now fully functional from extraction through Excel output
