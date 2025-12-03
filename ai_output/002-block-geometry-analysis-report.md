# Block Geometry Analysis Page - Feature Analysis

## Executive Summary

The Block Geometry Analysis sheet does **not** currently find blocks with unique dimensions. Instead, it lists **all blocks** with their native geometry (bounding box dimensions) and segment data. Each block appears once per layer where it's inserted, showing transformation data (rotations, scales) and the block's intrinsic geometry from its definition.

## Table Summary

| Column | Description | Source |
|--------|-------------|--------|
| Block Name | Name of the block definition | `block_layer_pairs` keys |
| Layer Name | Layer where block is inserted | `block_layer_pairs` keys |
| Rot 0° / 90° / 180° / 270° / Other | Insertion counts per rotation category | `block_rotation_counts` |
| Scale X / Scale Y | Single value or "VARIES" / "VARIES (-)" | `block_scale_data` |
| Native Width | Block bounding box width (drawing units) | `block_trimming_data` |
| Native Height | Block bounding box height (drawing units) | `block_trimming_data` |
| Vertical Segments | Comma-separated segment sizes (left→right) | Calculated from intersection points |
| Horizontal Segments | Comma-separated segment sizes (bottom→top) | Calculated from intersection points |

## Relevant Files

- **`app/core/excel_writer.py:520-681`** - `_create_block_geometry_analysis_sheet()` builds the DataFrame from extraction data
- **`app/core/geometry.py:23-110`** - `_get_block_bounding_box()` calculates native width/height from entity extents
- **`app/core/geometry.py:113-203`** - `_get_intersection_points()` extracts unique X/Y coordinates from block geometry
- **`app/core/geometry.py:206-239`** - `_calculate_segments()` computes distances between consecutive intersection points
- **`app/core/extractor.py:672-687`** - Populates `block_trimming_data` for each block definition
- **`app/core/types.py:115-132`** - `BlockTrimmingData` TypedDict defines the geometry data structure

## How the Data is Populated

### 1. Native Dimensions (Width/Height)

The extractor calls `_get_block_bounding_box()` on each block definition:

```
bbox = (min_x, min_y, max_x, max_y)
native_width = max_x - min_x
native_height = max_y - min_y
```

Supported entity types for bounding box calculation:
- LINE (start/end points)
- LWPOLYLINE / POLYLINE (vertex points)
- CIRCLE / ARC (center ± radius)
- POINT (location)

### 2. Segment Analysis

Segments represent distances between consecutive intersection points:

1. **Extract coordinates**: Collect all X and Y coordinates from block geometry
2. **Deduplicate**: Remove near-duplicates using epsilon tolerance (0.01)
3. **Sort**: Order coordinates ascending (X: left→right, Y: bottom→top)
4. **Calculate segments**: Distance between each consecutive pair

Example: For X coordinates `[0, 50, 1150, 1200]`, vertical segments = `[50, 1100, 50]`

### 3. Scale Display Logic

| Condition | Display Value |
|-----------|---------------|
| All insertions same scale | Numeric value (e.g., `1.0`) |
| Multiple positive scales | `VARIES` |
| Any negative scale present | `VARIES (-)` |

## Current Behavior vs. "Unique Dimensions"

**Current**: Lists every block-layer pair with its geometry data. Two blocks with identical dimensions (e.g., both 100x50) appear as separate rows.

**Not implemented**: Grouping/filtering blocks by unique dimension combinations. To find blocks with unique dimensions, users must manually filter/sort the Native Width and Native Height columns.

## Recommendations

To add "find unique dimensions" functionality, consider:

1. **Add unique dimension grouping**: New sheet or filter showing distinct (width, height) pairs with block counts
2. **Add dimension variance indicator**: Flag blocks that share dimensions with other blocks
3. **Add Excel conditional formatting**: Highlight duplicate dimension combinations

## Next Steps

- Clarify the specific use case for "unique dimensions" (identical blocks? similar sizes within tolerance?)
- Decide if this should be a new sheet, column, or filter in existing sheet
- Consider adding tolerance-based matching for "nearly identical" dimensions
