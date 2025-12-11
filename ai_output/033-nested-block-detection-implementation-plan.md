# Nested Block Detection Implementation Plan

## Executive Summary
This plan implements complete block definition tracking with nested block detection, ensuring 100% block coverage in extraction output. The implementation adds a new `BlockDefinitionRecord` TypedDict, scans block definitions for INSERT entities to detect nesting relationships, classifies blocks by insertion status (Inserted, Nested Only, Unused, System), and outputs a dedicated "Block Definitions" Excel sheet listing ALL blocks from the DXF file.

## Table Summary

| Unit | Scope | Risk | Key Files |
|------|-------|------|-----------|
| 1 | Types & Constants | Low | `types.py`, `constants.py` |
| 2 | Test Asset Creation | Low | `create_nested_block_test.py` |
| 3 | Extractor Nested Scanning | Medium | `extractor.py` |
| 4 | Excel Writer Block Definitions Sheet | Medium | `excel_writer.py`, `excel_formatting.py` |
| 5 | Unit Tests | Low | `test_extractor_nested.py`, `test_excel_writer_definitions.py` |

## Scope

### In Scope

1. List ALL block definitions from `doc.blocks` with insertion status in output
2. Detect nested block relationships by scanning for INSERT entities within block definitions
3. Add `BlockDefinitionRecord` TypedDict with: raw name, resolved name, insertion status, is_nested flag, parent block names, entity count
4. Create new "Block Definitions" Excel sheet listing every block definition
5. Add corresponding Excel column constants following naming conventions
6. Create test DXF asset with nested block scenarios
7. Implement unit tests for nested detection and Excel output

### Out of Scope

1. Recursive nesting depth calculation (only direct parent tracking)
2. XRef block special handling
3. Paperspace-only block detection
4. Dynamic block parameter visibility states
5. Modifications to existing Block Geometry Analysis sheet

## Relevant Files

- **`app/core/types.py`** - Add `BlockDefinitionRecord` TypedDict; existing TypedDicts follow established patterns (lines 124-246)
- **`app/core/constants.py`** - Add `EXCEL_SHEET_BLOCK_DEFINITIONS` and `EXCEL_COLUMN_BLOCK_*` constants (lines 16-116 for patterns)
- **`app/core/extractor.py`** - Modify block definition loop (lines 1143-1264) to scan for nested INSERTs and build `all_block_definitions`
- **`app/core/excel_writer.py`** - Add `_create_block_definitions_sheet()` function (pattern at lines 531-650)
- **`app/core/excel_formatting.py`** - Add `_format_block_definitions_sheet()` function
- **`app_docs/005-field-naming-convention.md`** - Field naming rules to follow

## Block Classification Rules

```
Block Name Pattern          -> Insertion Status
*Model_Space, *Paper_Space* -> "System"
*D* (e.g., *D1, *D23)       -> "System (Dimension)"
*X* (e.g., *X1, *X23)       -> "System (Hatch)"
*U* with XDATA resolution   -> Use resolved name, determine from insertions
*U* without resolution      -> "Unresolved (*U)"
A$C* with resolution        -> Use resolved name, determine from insertions
A$C* without resolution     -> "Unresolved (A$C)"
Regular blocks              -> "Inserted" / "Nested Only" / "Unused"
```

**Determination logic for regular/resolved blocks:**
- **"Inserted"**: Block appears in `block_counts` (has modelspace insertions)
- **"Nested Only"**: Block appears in `nested_block_parents` but NOT in `block_counts`
- **"Unused"**: Block appears in neither `block_counts` nor `nested_block_parents`

---

## Unit 1: Types & Constants (Low Risk)

### 1.1 Add BlockDefinitionRecord TypedDict

**File:** `app/core/types.py`

Add after `PolygonMetrics` TypedDict (around line 247):

```python
class BlockDefinitionRecord(TypedDict):
    """
    Complete record for a block definition with insertion and nesting status.

    Used in the all_block_definitions field of ExtractionResult to track
    every block definition in the DXF file regardless of insertion status.

    Attributes:
        block_raw_name: Original name from doc.blocks (e.g., "*U1", "DOOR")
        block_resolved_name: Resolved name (same as raw for non-anonymous blocks)
        block_insertion_status: One of "Inserted", "Nested Only", "Unused",
                               "System", "Unresolved (*U)", "Unresolved (A$C)"
        block_is_nested: True if this block is inserted inside another block definition
        block_nested_parent_names: List of parent block names containing this block
        block_entity_count: Number of entities in the block definition
    """

    block_raw_name: str
    block_resolved_name: str
    block_insertion_status: str
    block_is_nested: bool
    block_nested_parent_names: list[str]
    block_entity_count: int
```

### 1.2 Add Excel Constants

**File:** `app/core/constants.py`

Add after existing sheet constants (around line 24):

```python
EXCEL_SHEET_BLOCK_DEFINITIONS: str = "Block Definitions"
```

Add after existing column constants (around line 117):

```python
# Excel configuration - Block Definitions sheet columns
# See app_docs/005-field-naming-convention.md for naming conventions
EXCEL_COLUMN_BLOCK_RAW_NAME: str = "block_raw_name"
EXCEL_COLUMN_BLOCK_RESOLVED_NAME: str = "block_resolved_name"
EXCEL_COLUMN_BLOCK_INSERTION_STATUS: str = "block_insertion_status"
EXCEL_COLUMN_BLOCK_IS_NESTED: str = "block_is_nested"
EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: str = "block_nested_parent_names"
```

**Note:** `EXCEL_COLUMN_BLOCK_ENTITY_COUNT` already exists (line 29).

### 1.3 Update Imports

**File:** `app/core/types.py`

Update the module docstring Usage section to include `BlockDefinitionRecord`.

---

## Unit 2: Test Asset Creation (Low Risk)

### 2.1 Create Test DXF Generator Script

**File:** `app/tests/assets/create_nested_block_test.py`

```python
"""
Generate test DXF file with nested block scenarios for nested block detection testing.

This file creates blocks with various insertion patterns:

- OUTER_BLOCK: Contains INSERT of INNER_BLOCK
- INNER_BLOCK: Nested only (no modelspace insertion)
- STANDALONE_BLOCK: Inserted in modelspace, not nested
- UNUSED_BLOCK: Defined but never inserted anywhere
- MULTI_PARENT_BLOCK: Inserted in both OUTER_BLOCK and SECOND_OUTER
- SECOND_OUTER: Contains INSERT of MULTI_PARENT_BLOCK

System blocks (*Model_Space, *Paper_Space) exist automatically.

Expected output:
- OUTER_BLOCK: Inserted, is_nested=False, parents=[]
- INNER_BLOCK: Nested Only, is_nested=True, parents=["OUTER_BLOCK"]
- STANDALONE_BLOCK: Inserted, is_nested=False, parents=[]
- UNUSED_BLOCK: Unused, is_nested=False, parents=[]
- MULTI_PARENT_BLOCK: Inserted, is_nested=True, parents=["OUTER_BLOCK", "SECOND_OUTER"]
- SECOND_OUTER: Inserted, is_nested=False, parents=[]
- *Model_Space: System, is_nested=False, parents=[]
- *Paper_Space: System, is_nested=False, parents=[]
"""

import ezdxf


def create_nested_block_test() -> None:
    """Create DXF with nested block scenarios for detection testing."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Block 1: INNER_BLOCK - Will be nested inside OUTER_BLOCK only
    # Never inserted in modelspace directly
    block_inner = doc.blocks.new("INNER_BLOCK")
    block_inner.add_lwpolyline(
        [(0, 0), (20, 0), (20, 20), (0, 20)],
        close=True,
    )

    # Block 2: MULTI_PARENT_BLOCK - Will be nested in multiple parent blocks
    # Also inserted in modelspace
    block_multi = doc.blocks.new("MULTI_PARENT_BLOCK")
    block_multi.add_lwpolyline(
        [(0, 0), (15, 0), (15, 15), (0, 15)],
        close=True,
    )

    # Block 3: OUTER_BLOCK - Contains INSERT of INNER_BLOCK and MULTI_PARENT_BLOCK
    block_outer = doc.blocks.new("OUTER_BLOCK")
    block_outer.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
    )
    # Add nested block references
    block_outer.add_blockref("INNER_BLOCK", (10, 10))
    block_outer.add_blockref("MULTI_PARENT_BLOCK", (50, 50))

    # Block 4: SECOND_OUTER - Also contains INSERT of MULTI_PARENT_BLOCK
    block_second = doc.blocks.new("SECOND_OUTER")
    block_second.add_lwpolyline(
        [(0, 0), (80, 0), (80, 80), (0, 80)],
        close=True,
    )
    block_second.add_blockref("MULTI_PARENT_BLOCK", (30, 30))

    # Block 5: STANDALONE_BLOCK - Inserted in modelspace, not nested in any block
    block_standalone = doc.blocks.new("STANDALONE_BLOCK")
    block_standalone.add_lwpolyline(
        [(0, 0), (40, 0), (40, 40), (0, 40)],
        close=True,
    )

    # Block 6: UNUSED_BLOCK - Defined but never inserted anywhere
    block_unused = doc.blocks.new("UNUSED_BLOCK")
    block_unused.add_lwpolyline(
        [(0, 0), (30, 0), (30, 30), (0, 30)],
        close=True,
    )

    # Add block references to modelspace
    msp.add_blockref("OUTER_BLOCK", (0, 0))
    msp.add_blockref("STANDALONE_BLOCK", (150, 0))
    msp.add_blockref("SECOND_OUTER", (250, 0))
    msp.add_blockref("MULTI_PARENT_BLOCK", (400, 0))  # Direct modelspace insertion

    # Save the file
    doc.saveas("app/tests/assets/nested_block_test.dxf")
    print("Created app/tests/assets/nested_block_test.dxf")


if __name__ == "__main__":
    create_nested_block_test()
```

### 2.2 Generate Test Asset

Run the script to create the test DXF:

```bash
cd /workspace && python app/tests/assets/create_nested_block_test.py
```

---

## Unit 3: Extractor Nested Scanning (Medium Risk)

### 3.1 Add Nested Block Tracking Variables

**File:** `app/core/extractor.py`

At the top of `extract_blocks()` function, after existing variable declarations (around line 1125), add:

```python
# Track all block definitions and nested relationships
all_block_definitions: dict[str, BlockDefinitionRecord] = {}
nested_block_parents: dict[str, set[str]] = {}  # child_name -> {parent_names}
```

### 3.2 Scan for INSERT Entities Within Block Definitions

**File:** `app/core/extractor.py`

Modify the block definition loop (lines 1143-1264). After the entity count calculation (around line 1231), add INSERT entity scanning:

```python
# Scan block definition for nested INSERT entities
for entity in block_def:
    if entity.dxftype() == "INSERT":
        nested_name = entity.dxf.name
        # Resolve anonymous block names if mapping exists
        if nested_name in anonymous_to_resolved:
            nested_name = anonymous_to_resolved[nested_name]
        # Track parent relationship
        if nested_name not in nested_block_parents:
            nested_block_parents[nested_name] = set()
        nested_block_parents[nested_name].add(effective_name)
```

### 3.3 Build All Block Definitions After Modelspace Scan

**File:** `app/core/extractor.py`

After the modelspace entity loop completes (after line ~1480), add a second pass through `doc.blocks` to build `all_block_definitions`:

```python
# Build complete block definition records after modelspace scan
# This must happen AFTER block_counts is populated
logger.info("Building complete block definition records...")

def _classify_block_insertion_status(
    block_name: str,
    raw_name: str,
    block_counts: dict[str, int],
    nested_parents: dict[str, set[str]],
) -> str:
    """Determine insertion status for a block."""
    # System blocks
    if raw_name in ("*Model_Space", "*Paper_Space") or raw_name.startswith("*Paper_Space"):
        return "System"
    if raw_name.startswith("*D") and len(raw_name) > 2 and raw_name[2:].isdigit():
        return "System (Dimension)"
    if raw_name.startswith("*X") and len(raw_name) > 2 and raw_name[2:].isdigit():
        return "System (Hatch)"

    # Unresolved anonymous blocks
    if raw_name.startswith("*U") and raw_name not in anonymous_to_resolved:
        return "Unresolved (*U)"
    if raw_name.startswith("A$C"):
        resolved = anonymous_to_resolved.get(raw_name)
        if resolved is None or resolved == raw_name:
            return "Unresolved (A$C)"

    # Regular/resolved blocks - check insertion status
    if block_name in block_counts:
        return "Inserted"
    if block_name in nested_parents:
        return "Nested Only"
    return "Unused"

for block_def in doc.blocks:
    raw_name = block_def.name

    # Determine effective (resolved) name
    if raw_name in anonymous_to_resolved:
        effective_name = anonymous_to_resolved[raw_name]
    else:
        effective_name = raw_name

    # Count entities
    entity_count = sum(1 for _ in block_def)

    # Get parent names
    parent_names = list(nested_block_parents.get(effective_name, set()))
    parent_names.sort()  # Consistent ordering

    # Determine insertion status
    insertion_status = _classify_block_insertion_status(
        effective_name,
        raw_name,
        block_counts,
        nested_block_parents,
    )

    # Build record
    all_block_definitions[raw_name] = {
        "block_raw_name": raw_name,
        "block_resolved_name": effective_name,
        "block_insertion_status": insertion_status,
        "block_is_nested": effective_name in nested_block_parents,
        "block_nested_parent_names": parent_names,
        "block_entity_count": entity_count,
    }

logger.info(f"Tracked {len(all_block_definitions)} total block definitions")
```

### 3.4 Add to ExtractionResult Return

**File:** `app/core/extractor.py`

In the return statement (around line 1530), add:

```python
"all_block_definitions": all_block_definitions,
"nested_block_parents": {k: list(v) for k, v in nested_block_parents.items()},
```

### 3.5 Update ExtractionResult Type Hints

If `ExtractionResult` is defined as a TypedDict, add the new fields. If using dict return type, document the new keys in the docstring.

---

## Unit 4: Excel Writer Block Definitions Sheet (Medium Risk)

### 4.1 Add Sheet Creation Function

**File:** `app/core/excel_writer.py`

Add new function after `_create_block_geometry_analysis_sheet()`:

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
        # Format parent names as comma-separated string
        parent_names_str = ", ".join(record["block_nested_parent_names"])

        rows.append({
            EXCEL_COLUMN_BLOCK_RAW_NAME: record["block_raw_name"],
            EXCEL_COLUMN_BLOCK_RESOLVED_NAME: record["block_resolved_name"],
            EXCEL_COLUMN_BLOCK_INSERTION_STATUS: record["block_insertion_status"],
            EXCEL_COLUMN_BLOCK_IS_NESTED: record["block_is_nested"],
            EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES: parent_names_str,
            EXCEL_COLUMN_BLOCK_ENTITY_COUNT: record["block_entity_count"],
        })

    # Sort by insertion status (Inserted first, then Nested Only, Unused, System last)
    # Then by resolved name within each status
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

    # Write to Excel
    df.to_excel(writer, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS, index=False)
    logger.info(f"Created Block Definitions sheet with {len(rows)} block definitions")
```

### 4.2 Add Formatting Function

**File:** `app/core/excel_formatting.py`

Add function to format the new sheet:

```python
def _format_block_definitions_sheet(workbook: Workbook) -> None:
    """Apply formatting to the Block Definitions sheet."""
    if EXCEL_SHEET_BLOCK_DEFINITIONS not in workbook.sheetnames:
        return

    ws = workbook[EXCEL_SHEET_BLOCK_DEFINITIONS]

    # Format headers
    for cell in ws[1]:
        cell.value = format_header(cell.value) if cell.value else cell.value
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

    # Auto-fit column widths
    for column_cells in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column_cells[0].column)
        for cell in column_cells:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except (TypeError, AttributeError):
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Apply conditional formatting for boolean is_nested column
    # Find the is_nested column
    is_nested_col = None
    for idx, cell in enumerate(ws[1], 1):
        if cell.value and "nested" in str(cell.value).lower() and "parent" not in str(cell.value).lower():
            is_nested_col = get_column_letter(idx)
            break

    if is_nested_col:
        # Highlight nested blocks
        for row in range(2, ws.max_row + 1):
            cell = ws[f"{is_nested_col}{row}"]
            if cell.value is True:
                cell.fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
```

### 4.3 Call Functions from Main Writer

**File:** `app/core/excel_writer.py`

In `write_excel_output()`, add call to create the new sheet:

```python
_create_block_definitions_sheet(data, writer)
```

**File:** `app/core/excel_formatting.py`

In `format_excel_output()`, add call to format the new sheet:

```python
_format_block_definitions_sheet(workbook)
```

### 4.4 Update Imports

**File:** `app/core/excel_writer.py`

Add to imports:

```python
from core.constants import (
    # ... existing imports ...
    EXCEL_SHEET_BLOCK_DEFINITIONS,
    EXCEL_COLUMN_BLOCK_RAW_NAME,
    EXCEL_COLUMN_BLOCK_RESOLVED_NAME,
    EXCEL_COLUMN_BLOCK_INSERTION_STATUS,
    EXCEL_COLUMN_BLOCK_IS_NESTED,
    EXCEL_COLUMN_BLOCK_NESTED_PARENT_NAMES,
)
```

---

## Unit 5: Unit Tests (Low Risk)

### 5.1 Create Extractor Nested Detection Tests

**File:** `app/tests/core/extractor/test_extractor_nested.py`

```python
"""
Unit tests for nested block detection functionality in the extractor module.

Tests verify that:
1. All block definitions appear in all_block_definitions output
2. Nested blocks are correctly identified
3. Parent block names are tracked
4. Insertion statuses are correctly assigned
"""

import pytest
from core.extractor import extract_blocks


class TestNestedBlockDetection:
    """Test suite for nested block detection."""

    @pytest.fixture
    def nested_result(self) -> dict:
        """Extract nested block test DXF."""
        return extract_blocks("app/tests/assets/nested_block_test.dxf")

    def test_all_block_definitions_key_exists(self, nested_result: dict) -> None:
        """Test that all_block_definitions key exists in extraction result."""
        assert "all_block_definitions" in nested_result
        assert isinstance(nested_result["all_block_definitions"], dict)

    def test_all_blocks_coverage(self, nested_result: dict) -> None:
        """Test that every doc.blocks entry appears in output."""
        all_defs = nested_result["all_block_definitions"]

        # Should include system blocks
        assert "*Model_Space" in all_defs
        assert "*Paper_Space" in all_defs

        # Should include all user blocks
        assert "OUTER_BLOCK" in all_defs
        assert "INNER_BLOCK" in all_defs
        assert "STANDALONE_BLOCK" in all_defs
        assert "UNUSED_BLOCK" in all_defs
        assert "MULTI_PARENT_BLOCK" in all_defs
        assert "SECOND_OUTER" in all_defs

    def test_nested_block_detection(self, nested_result: dict) -> None:
        """Test that INNER_BLOCK is detected as nested inside OUTER_BLOCK."""
        all_defs = nested_result["all_block_definitions"]
        inner = all_defs["INNER_BLOCK"]

        assert inner["block_is_nested"] is True
        assert "OUTER_BLOCK" in inner["block_nested_parent_names"]

    def test_nested_parent_names_multiple(self, nested_result: dict) -> None:
        """Test that blocks nested in multiple parents track all parents."""
        all_defs = nested_result["all_block_definitions"]
        multi = all_defs["MULTI_PARENT_BLOCK"]

        assert multi["block_is_nested"] is True
        assert "OUTER_BLOCK" in multi["block_nested_parent_names"]
        assert "SECOND_OUTER" in multi["block_nested_parent_names"]

    def test_insertion_status_inserted(self, nested_result: dict) -> None:
        """Test that blocks with modelspace insertions have status 'Inserted'."""
        all_defs = nested_result["all_block_definitions"]

        assert all_defs["OUTER_BLOCK"]["block_insertion_status"] == "Inserted"
        assert all_defs["STANDALONE_BLOCK"]["block_insertion_status"] == "Inserted"
        assert all_defs["MULTI_PARENT_BLOCK"]["block_insertion_status"] == "Inserted"

    def test_insertion_status_nested_only(self, nested_result: dict) -> None:
        """Test that blocks only nested in other blocks have status 'Nested Only'."""
        all_defs = nested_result["all_block_definitions"]
        inner = all_defs["INNER_BLOCK"]

        assert inner["block_insertion_status"] == "Nested Only"

    def test_insertion_status_unused(self, nested_result: dict) -> None:
        """Test that blocks never inserted anywhere have status 'Unused'."""
        all_defs = nested_result["all_block_definitions"]
        unused = all_defs["UNUSED_BLOCK"]

        assert unused["block_insertion_status"] == "Unused"

    def test_insertion_status_system(self, nested_result: dict) -> None:
        """Test that system blocks have status 'System'."""
        all_defs = nested_result["all_block_definitions"]

        assert all_defs["*Model_Space"]["block_insertion_status"] == "System"
        assert all_defs["*Paper_Space"]["block_insertion_status"] == "System"

    def test_entity_count_populated(self, nested_result: dict) -> None:
        """Test that entity counts are populated for all blocks."""
        all_defs = nested_result["all_block_definitions"]

        for raw_name, record in all_defs.items():
            assert "block_entity_count" in record
            assert isinstance(record["block_entity_count"], int)
            assert record["block_entity_count"] >= 0

    def test_non_nested_blocks_have_empty_parents(self, nested_result: dict) -> None:
        """Test that non-nested blocks have empty parent names list."""
        all_defs = nested_result["all_block_definitions"]

        assert all_defs["OUTER_BLOCK"]["block_nested_parent_names"] == []
        assert all_defs["STANDALONE_BLOCK"]["block_nested_parent_names"] == []
        assert all_defs["UNUSED_BLOCK"]["block_nested_parent_names"] == []
```

### 5.2 Create Excel Writer Tests

**File:** `app/tests/core/excel_writer/test_excel_writer_definitions.py`

```python
"""
Unit tests for Block Definitions sheet creation in the excel_writer module.

Tests verify that:
1. Block Definitions sheet is created
2. All expected columns exist
3. All blocks from extraction appear in the sheet
"""

import pandas as pd
import pytest
from openpyxl import load_workbook

from core.constants import EXCEL_SHEET_BLOCK_DEFINITIONS
from core.excel_writer import write_excel_output
from core.extractor import extract_blocks


class TestBlockDefinitionsSheet:
    """Test suite for Block Definitions sheet creation."""

    @pytest.fixture
    def excel_output_path(self, tmp_path) -> str:
        """Generate Excel output from nested block test."""
        result = extract_blocks("app/tests/assets/nested_block_test.dxf")
        output_path = str(tmp_path / "test_output.xlsx")
        write_excel_output(result, output_path)
        return output_path

    def test_block_definitions_sheet_created(self, excel_output_path: str) -> None:
        """Test that Block Definitions sheet exists in output."""
        wb = load_workbook(excel_output_path)
        assert EXCEL_SHEET_BLOCK_DEFINITIONS in wb.sheetnames

    def test_block_definitions_columns(self, excel_output_path: str) -> None:
        """Test that expected columns exist in Block Definitions sheet."""
        df = pd.read_excel(excel_output_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

        # Check for expected columns (Title Case after formatting)
        expected_columns = [
            "Block Raw Name",
            "Block Resolved Name",
            "Block Insertion Status",
            "Block Is Nested",
            "Block Nested Parent Names",
            "Block Entity Count",
        ]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_block_definitions_all_blocks(self, excel_output_path: str) -> None:
        """Test that all blocks appear in Block Definitions sheet."""
        df = pd.read_excel(excel_output_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

        raw_names = df["Block Raw Name"].tolist()

        # User blocks
        assert "OUTER_BLOCK" in raw_names
        assert "INNER_BLOCK" in raw_names
        assert "STANDALONE_BLOCK" in raw_names
        assert "UNUSED_BLOCK" in raw_names

        # System blocks
        assert "*Model_Space" in raw_names
        assert "*Paper_Space" in raw_names

    def test_block_definitions_row_count(self, excel_output_path: str) -> None:
        """Test that row count matches total block count."""
        result = extract_blocks("app/tests/assets/nested_block_test.dxf")
        df = pd.read_excel(excel_output_path, sheet_name=EXCEL_SHEET_BLOCK_DEFINITIONS)

        expected_count = len(result["all_block_definitions"])
        assert len(df) == expected_count
```

---

## Verification Checklist

After implementation, verify:

- [ ] `len(all_block_definitions) == len(list(doc.blocks))` for any DXF file
- [ ] System blocks (`*Model_Space`, `*Paper_Space`) appear with status "System"
- [ ] Unresolved `*U` blocks appear with status "Unresolved (*U)"
- [ ] Nested blocks have `block_is_nested=True` and correct parent names
- [ ] Unused blocks (defined but never inserted) appear with status "Unused"
- [ ] Blocks inserted in modelspace have status "Inserted"
- [ ] Excel "Block Definitions" sheet lists EVERY block from the DXF
- [ ] All unit tests pass

---

## Implementation Order

Execute units in this exact sequence:

1. **Unit 1** - Types & Constants (no dependencies)
2. **Unit 2** - Test Asset Creation (depends on nothing)
3. **Unit 3** - Extractor Nested Scanning (depends on Unit 1)
4. **Unit 4** - Excel Writer (depends on Units 1 and 3)
5. **Unit 5** - Unit Tests (depends on Units 2, 3, and 4)

---

## Technical References

- [ezdxf Block Documentation](https://ezdxf.readthedocs.io/en/stable/blocks/block.html)
- [ezdxf Blocks Tutorial](https://ezdxf.readthedocs.io/en/stable/tutorials/blocks.html)
- Field naming conventions: `app_docs/005-field-naming-convention.md`
- Existing TypedDict patterns: `app/core/types.py:124-246`
- Existing Excel sheet patterns: `app/core/excel_writer.py:531-650`
- Existing test patterns: `app/tests/core/extractor/test_extractor_dynamic.py`
