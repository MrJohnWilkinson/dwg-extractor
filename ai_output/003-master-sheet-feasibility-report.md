# Master Sheet Feasibility Report

## Executive Summary
A master sheet combining all CAD extraction data into a single filterable view is **technically feasible** and would significantly improve user experience. The recommended approach is a denormalized "fact table" design with a `record_type` discriminator column, allowing users to filter progressively. Implementation requires careful attention to DRY principles through shared data transformation utilities.

## Table Summary

| Aspect | Current State | Master Sheet Impact | Recommendation |
|--------|--------------|---------------------|----------------|
| **Sheets** | 7 separate sheets | 1 master + 7 detail sheets | Add master as first sheet |
| **Row granularity** | Mixed (blocks, layers, entities) | Unified with `record_type` column | Denormalized fact table |
| **Code reuse** | Each sheet has dedicated function | Risk of duplication | Extract shared row builders |
| **User filtering** | Switch sheets manually | Progressive Excel filters | High UX improvement |
| **Implementation effort** | N/A | Medium | 2 new functions + refactor |
| **Technical debt risk** | Low | Medium if done wrong | Mitigate with shared utilities |

## Relevant Files

- `app/core/excel_writer.py` - Contains 7 sheet creation functions (`_create_*_sheet`) that would need refactoring to share row-building logic with master sheet
- `app/core/extractor.py` - Defines `ExtractionResult` TypedDict containing all data; no changes needed
- `app/core/types.py` - Defines frozen dataclass keys (`BlockLayerKey`, `AnnotationKey`, etc.); may need `MasterRecordType` enum
- `app/core/constants.py` - Excel column name constants; needs new master sheet constants
- `app/core/excel_formatting.py` - Sheet formatting functions; needs `_format_master_sheet()` function

## Current Architecture Analysis

### Data Domains (7 Sheets)
1. **Block Analysis** - Block-layer pairs with insertion counts (primary inventory)
2. **Layer Analysis** - Layer-level aggregates (insertion counts, entity counts, colors)
3. **Entity Summary** - Global entity type counts (e.g., INSERT: 500, LINE: 2000)
4. **Block Geometry Analysis** - Block transformations (rotations, scales, dimensions)
5. **Annotations Analysis** - TEXT/MTEXT content with colors
6. **Color Analysis** - Entity colors grouped by RGB/layer/type
7. **Extraction Issues** - Unresolved anonymous blocks

### Data Granularity Challenge
Each sheet operates at a different level of aggregation:
- **Block-level**: Block Analysis, Block Geometry Analysis
- **Layer-level**: Layer Analysis
- **Entity-level**: Entity Summary (aggregated), Annotations Analysis (individual)
- **Color-level**: Color Analysis (individual entities)
- **Issue-level**: Extraction Issues

## Recommended Design: Denormalized Master Sheet

### Schema Design
```
| Record Type | Block Name | Layer Name | Count | Entity Type | Contents | R | G | B | Scale X | Scale Y | ... |
|-------------|------------|------------|-------|-------------|----------|---|---|---|---------|---------|-----|
| Block       | DOOR       | WALLS      | 45    | -           | -        | - | - | - | 1.0     | 1.0     | ... |
| Layer       | -          | WALLS      | 1200  | -           | -        | - | - | - | -       | -       | ... |
| Entity      | -          | -          | 500   | INSERT      | -        | - | - | - | -       | -       | ... |
| Annotation  | -          | NOTES      | 5     | TEXT        | DOOR     |255| 0 | 0 | -       | -       | ... |
| Color       | -          | WALLS      | 45    | Lines       | -        |255| 0 | 0 | -       | -       | ... |
| Issue       | *U3        | FIXTURES   | 5     | -           | No XDATA | - | - | - | -       | -       | ... |
```

### Key Design Decisions

1. **Record Type Discriminator Column** - First column identifies row type, enabling filter-based navigation
2. **Superset of All Columns** - Include all columns from all sheets; use `-` or blank for non-applicable fields
3. **Sort Order** - Group by record type, then by primary sort within each type
4. **Conditional Formatting** - Apply same highlighting rules (scale variance, issue highlighting)

## DRY Implementation Strategy

### Current Problem: Duplicated Row-Building Logic
Each `_create_*_sheet()` function builds DataFrames independently. Adding a master sheet would duplicate this logic.

### Solution: Shared Row Builder Functions

```python
# New module: app/core/master_sheet.py or refactor into excel_writer.py

def _build_block_rows(data: ExtractionResult) -> list[dict[str, Any]]:
    """Build row dictionaries for block analysis data."""
    # Extracted from _create_block_analysis_sheet()
    ...

def _build_layer_rows(data: ExtractionResult) -> list[dict[str, Any]]:
    """Build row dictionaries for layer analysis data."""
    # Extracted from _create_layer_analysis_sheet()
    ...

# Pattern repeats for all 7 data types
```

### Refactored Sheet Creation

```python
def _create_block_analysis_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    rows = _build_block_rows(data)  # Reusable
    df = pd.DataFrame(rows)
    # Sheet-specific formatting and sorting
    ...

def _create_master_sheet(data: ExtractionResult, writer: pd.ExcelWriter) -> None:
    # Combine all row builders with record_type tagging
    all_rows = []
    all_rows.extend([{**row, "record_type": "Block"} for row in _build_block_rows(data)])
    all_rows.extend([{**row, "record_type": "Layer"} for row in _build_layer_rows(data)])
    # ... etc for all 7 types
    df = pd.DataFrame(all_rows)
    ...
```

## Technical Debt Prevention

### Do
- Extract row-building logic into reusable functions
- Use a `RecordType` enum for type safety
- Add master sheet constants to `constants.py` following naming convention
- Write tests for row builders independently of sheet creation
- Document column mappings between record types

### Don't
- Copy-paste existing sheet creation code
- Add master-specific logic scattered throughout existing functions
- Create special cases in formatting functions
- Skip the refactor and create duplicate logic

## Column Mapping Strategy

| Master Column | Block | Layer | Entity | Annotation | Color | Issue |
|--------------|-------|-------|--------|------------|-------|-------|
| `record_type` | "Block" | "Layer" | "Entity" | "Annotation" | "Color" | "Issue" |
| `block_name` | block_name | - | - | - | - | issue_block_name |
| `layer_name` | block_layer_name | layer_name | - | annotation_layer_name | color_layer_name | issue_layer_name |
| `count` | block_insertion_count | layer_entity_count | entity_type_count | annotation_count | color_entity_count | issue_insertion_count |
| `entity_type` | - | - | entity_type_name | annotation_type | color_entity_type | - |
| `contents` | - | - | - | annotation_contents | color_annotation_contents | issue_details |
| `color_r` | - | - | - | annotation_color_r | color_red | - |
| `color_g` | - | - | - | annotation_color_g | color_green | - |
| `color_b` | - | - | - | annotation_color_b | color_blue | - |
| `scale_x` | - | - | - | - | - | - |
| `scale_y` | - | - | - | - | - | - |

*Note: Block Geometry data can be joined to Block rows or kept as separate "Geometry" record type*

## User Experience Benefits

1. **Single View** - See all extraction data without switching sheets
2. **Progressive Filtering** - Filter by `record_type` first, then by specific attributes
3. **Cross-Domain Search** - Find all references to a layer name across blocks, annotations, colors
4. **Export Simplicity** - Copy single sheet for downstream analysis

## Recommendations

1. **Phase 1: Refactor Row Builders** - Extract `_build_*_rows()` functions from existing code (low risk)
2. **Phase 2: Add Master Sheet** - Create `_create_master_sheet()` using shared builders (medium risk)
3. **Phase 3: Test Coverage** - Add unit tests for row builders and master sheet generation
4. **Consider**: Make master sheet optional via configuration flag for backward compatibility

## Next Steps

1. Create specification document for master sheet implementation
2. Define complete column list and mapping for all 7 record types
3. Identify which Block Geometry columns should be merged vs. separate record type
4. Decide on empty cell representation (`-`, blank, or `N/A`)
5. Design conditional formatting rules for master sheet
