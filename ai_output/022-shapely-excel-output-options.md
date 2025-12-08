# Shapely Geometry Data Display Options for Excel Output

## Executive Summary

The Shapely refactor calculates valuable polygon data (counts, areas, dimensions) that is currently only logged internally. This report analyzes options for exposing this data in the Block Geometry Analysis sheet, focusing on fields users can easily verify by visually inspecting CAD block drawings.

## Table Summary

| Field | User Verifiable? | Implementation Effort | Value to User |
|-------|------------------|----------------------|---------------|
| `block_content_zone_width` | Yes - measure largest rect | Low | High |
| `block_content_zone_height` | Yes - measure largest rect | Low | High |
| `block_content_zone_area` | Yes - calculate W x H | Low | Medium |
| `block_polygon_count` | Yes - count shapes | Low | High |
| `block_line_segment_count` | Yes - count lines | Low | Medium |
| `block_largest_polygon_area` | Moderate - requires math | Medium | Medium |
| `block_lwpolyline_count` | Yes - count polylines | Low | Medium |
| `block_line_cycle_count` | Moderate - trace cycles | Low | Medium |
| `block_skip_reason` | N/A - diagnostic | Low | High |

## Relevant Files

- **`app/core/geometry.py`** - Contains `_detect_content_zone()` which calculates polygon counts, net areas, and bounding boxes. Lines 630-740 are the main detection logic.
- **`app/core/types.py`** - Defines `ContentZoneData` TypedDict (lines 195-219). Would need extension to include new fields.
- **`app/core/constants.py`** - Contains Excel column name constants (lines 104-111). New columns would be added here.
- **`app/core/excel_writer.py`** - `_create_block_geometry_analysis_sheet()` (lines 527-714) builds the DataFrame. Would need modification to include new fields.

## Currently Calculated but Not Exposed

The following data is calculated during content zone detection but only logged:

1. **`polygon_count`** - Total shapes (LWPOLYLINE + LINE cycles)
2. **`line_count`** - Number of LINE segments in block
3. **`len(lwpolyline_shapes)`** - Closed LWPOLYLINE count
4. **`len(line_cycle_shapes)`** - LINE cycles found by polygonize
5. **`max_net_area`** - Largest polygon's net area (after subtracting contained shapes)
6. **`len(tied_shapes)`** - Count of polygons tied for largest area
7. **Content zone bounding box** - `cz_min_x, cz_min_y, cz_max_x, cz_max_y`

## Recommended New Columns

### Tier 1: High Value, Easy to Verify

| Column Name | Description | User Verification |
|-------------|-------------|-------------------|
| `block_content_zone_width` | Width of detected content zone | Measure the main rectangle in CAD |
| `block_content_zone_height` | Height of detected content zone | Measure the main rectangle in CAD |
| `block_polygon_count` | Total closed shapes detected | Count rectangles/polylines in block |

**Rationale**: Users can open a block in AutoCAD and immediately verify these values. Width/height are measurable, and polygon count is countable.

### Tier 2: Medium Value, Diagnostic

| Column Name | Description | User Verification |
|-------------|-------------|-------------------|
| `block_line_segment_count` | LINE entities in block definition | Count LINE entities (tedious but possible) |
| `block_content_zone_area` | Area of content zone (W x H) | Calculate from width/height |
| `block_skip_reason` | Why content zone was skipped | Understand "Not Detected" cases |

**Rationale**: Line count helps users understand why complex blocks might be skipped. Skip reason provides transparency when detection fails.

### Tier 3: Advanced, Lower Priority

| Column Name | Description | User Verification |
|-------------|-------------|-------------------|
| `block_lwpolyline_count` | Closed LWPOLYLINE shapes | Filter entities by type in CAD |
| `block_line_cycle_count` | Polygons from LINE segments | Requires tracing connected lines |
| `block_largest_polygon_area` | Net area of content zone | Requires calculating area minus holes |

## Implementation Approach

### Option A: Extend ContentZoneData (Recommended)

Add fields to the existing `ContentZoneData` TypedDict:

```python
class ContentZoneData(TypedDict):
    # Existing fields...
    suggested_trim_left: float | None
    suggested_trim_right: float | None
    suggested_trim_top: float | None
    suggested_trim_bottom: float | None
    content_zone_detected: bool

    # New Tier 1 fields
    content_zone_width: float | None
    content_zone_height: float | None
    polygon_count: int

    # New Tier 2 fields (optional)
    line_segment_count: int
    content_zone_area: float | None
    skip_reason: str | None  # e.g., "Too many polygons (532 > 500)"
```

### Option B: Separate Geometry Stats TypedDict

Create a dedicated `GeometryStats` TypedDict for diagnostic data, keeping `ContentZoneData` focused on trim values.

### Option C: Conditional Column Display

Add columns only when content zone is detected (sparse columns). Less clutter but inconsistent Excel structure.

## Excel Sheet Organization

### Current Block Geometry Analysis Columns (18)

```
block_name | block_layer_name | rotations (5) | scales (2) | dimensions (2) | segments (2) | trims (4) | detected (1)
```

### Proposed Column Groupings

**Group 1: Identity**
- `block_name`, `block_layer_name`

**Group 2: Transformations**
- `block_rotation_0/90/180/270/other`, `block_scale_x/y`

**Group 3: Block Dimensions**
- `block_native_width`, `block_native_height`

**Group 4: Shape Statistics (NEW)**
- `block_polygon_count`, `block_line_segment_count`

**Group 5: Content Zone Geometry (NEW)**
- `block_content_zone_width`, `block_content_zone_height`, `block_content_zone_area`

**Group 6: Trim Values**
- `block_suggested_trim_left/right/top/bottom`

**Group 7: Detection Status**
- `block_content_zone_detected`, `block_skip_reason`

**Group 8: Segments (existing)**
- `block_vertical_segments`, `block_horizontal_segments`

## Skip Reason Values

When content zone detection is skipped or fails, provide clear reasons:

| Condition | Skip Reason Value |
|-----------|-------------------|
| No closed shapes found | "No closed polygons" |
| Too many LINE segments | "Line segments exceed 5000" |
| Too many polygons | "Polygons exceed 500" |
| Zero/negative area | "Content zone has zero area" |
| Successful detection | `null` or empty |

## Recommendations

1. **Start with Tier 1 columns** - `block_content_zone_width`, `block_content_zone_height`, `block_polygon_count` provide immediate value
2. **Add `block_skip_reason`** - Transparency for users investigating "Not Detected" blocks
3. **Group related columns** - Reorganize sheet for logical flow: Identity → Stats → Geometry → Trims → Status
4. **Consider conditional formatting** - Highlight rows where `polygon_count` approaches thresholds (e.g., >400)

## Next Steps

1. Create feature spec for Tier 1 columns (`/dev:feature`)
2. Extend `ContentZoneData` TypedDict with new fields
3. Modify `_detect_content_zone()` to calculate and return new values
4. Update `_create_block_geometry_analysis_sheet()` to include new columns
5. Add new column constants to `constants.py`
6. Update tests to verify new fields
