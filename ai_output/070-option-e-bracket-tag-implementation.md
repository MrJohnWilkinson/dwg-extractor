# Option E Implementation: Bracket Tags in Attribute Analysis Sheet

## Executive Summary

The Attribute Analysis sheet already exists with a vertical filterable layout. Implementing Option E requires only ONE code change: wrap the tag value with square brackets. The user can then copy the Tag column, use Excel's Paste Special → Transpose to get a horizontal row of `[TAG1]`, `[TAG2]`, etc.

## Table Summary

| Item | Current State | Proposed Change | Effort |
|------|---------------|-----------------|--------|
| Tag Column Format | `GUIDE` | `[GUIDE]` | 1 line |
| Sheet Structure | Already vertical/filterable | No change needed | None |
| Test Updates | Expect `GUIDE` | Expect `[GUIDE]` | ~3 assertions |
| Total Changes | - | 1 code file, 1 test file | Minimal |

## Relevant Files

- **app/core/excel_writer.py:1419** - The single line that sets the tag value; change `tag` to `f"[{tag}]"`
- **app/tests/core/excel_writer/test_excel_writer_attribute_analysis.py** - Update test assertions expecting bracket format (if exists)
- **app/tests/core/extractor/test_extractor_attributes.py** - Verify no impact (extraction unchanged)

## Current Implementation

The Attribute Analysis sheet (line 1356-1429 in excel_writer.py) already:
- Groups by (block_name, tag) → set of values
- Creates vertical rows with Block Name, Layer Names, Tag, Values, Count
- Supports Excel filtering on all columns

**Current output:**
```
│ Block Name    │ Layer Names │ Tag   │ Values        │ Count │
│ PRODUCT_BLOCK │ TEST_LAYER  │ GUIDE │ A, B, C       │ 3     │
│ PRODUCT_BLOCK │ TEST_LAYER  │ PRICE │ 9.99, 19.99   │ 2     │
```

**After change:**
```
│ Block Name    │ Layer Names │ Tag     │ Values        │ Count │
│ PRODUCT_BLOCK │ TEST_LAYER  │ [GUIDE] │ A, B, C       │ 3     │
│ PRODUCT_BLOCK │ TEST_LAYER  │ [PRICE] │ 9.99, 19.99   │ 2     │
```

## Implementation Steps

### Step 1: Modify excel_writer.py (1 line)

**File:** `app/core/excel_writer.py`
**Line:** 1419

```python
# FROM:
EXCEL_COLUMN_ATTRIBUTE_TAG: tag,

# TO:
EXCEL_COLUMN_ATTRIBUTE_TAG: f"[{tag}]",
```

### Step 2: Update Tests (if needed)

Check and update any test assertions that verify the tag format in the Attribute Analysis sheet.

### Step 3: Validate

```bash
uv run mypy app/core/excel_writer.py
uv run pytest app/tests/core/excel_writer/ -v -k "attribute"
uv run pytest app/tests/ -v
```

## User Workflow After Implementation

1. Open Excel output file
2. Go to "Attribute Analysis" sheet
3. Filter/sort the Tag column as needed
4. Select cells in Tag column (e.g., C2:C10)
5. Copy (Ctrl+C)
6. Go to destination, right-click → Paste Special → Transpose
7. Result: `[GUIDE]  [PRICE]  [SKU]  ...` in a horizontal row

## Simple List Summary

- **Only 1 line of code change needed** - wrap `tag` with `f"[{tag}]"` at line 1419
- Sheet already exists with vertical filterable layout
- No new sheets, columns, or structural changes required
- Test updates: change expected values from `GUIDE` to `[GUIDE]`
- User copies Tag column → Paste Special → Transpose for horizontal output
