# Block Suggested Trim Left 779 Analysis

## Executive Summary

The `Block Suggested Trim Left` value of 779 for `Refrigeration_Frozen_Hussmann_PGL_2050H - 5 Door-82274016-GROUND FFL` is caused by a **discrepancy between two different bounding box calculations**: the block bounding box uses **full circle extents for ARC entities** (simplified approximation), while the content zone detection uses **actual flattened arc geometry**. This creates a 779-unit difference at the left edge.

## Table Summary

| Calculation Step | Method | min_x Value | Notes |
|-----------------|--------|-------------|-------|
| Block Bounding Box | Full circle extents for ARCs | -779.00 | ARC center (0, -952.65) - radius (779) = -779 |
| Edge Extraction | Flattened arc geometry | 0.00 | Arc start point at x=0 (270° angle) |
| Paint Bucket Regions | 99 polygons detected | -50.00 | Some small LINE entities at x=-50 |
| After min_area_filter | 10 polygons survive | 0.00 | Small polygons filtered out |
| **trim_left** | cz_min_x - block_min_x | **779.00** | 0 - (-779) = 779 |

## Relevant Files

- `app/core/geometry.py:242-250` - `_get_block_bounding_box()` uses full circle extents for ARC entities
- `app/core/geometry.py:577-601` - `_extract_arc_edges()` flattens arcs using actual geometry via `entity.flattening()`
- `app/core/geometry.py:1426` - trim_left calculation: `cz_min_x - block_min_x`
- `app/tests/core/test_content_zone.py` - Content zone detection tests (none specifically for this ARC bbox discrepancy scenario)

## Root Cause Analysis

### The Block Contains 5 ARCs

All ARCs have the same geometry pattern:
- **Radius**: 779 units
- **Angle span**: 270° to 356.10° (86.10° arc)
- **Arc length**: ~1170.57 units each

The leftmost arc (ARC 35):
```
Center: (0.00, -952.65)
Radius: 779.00
Start angle: 270°  → Start point: (0.00, -1731.65)
End angle: 356.10° → End point: (777.19, -1005.68)
```

### Step-by-Step Calculation Trace

**Step 1: Block Bounding Box Calculation** (`_get_block_bounding_box`)

For ARC entities, the code uses **simplified full circle extents**:
```python
elif entity_type == "ARC":
    center = entity.dxf.center
    radius = entity.dxf.radius
    # Simplified bounding box for arcs (use full circle extents)
    min_x = min(min_x, center.x - radius)  # 0 - 779 = -779
```

Result: `block_min_x = -779`

**Step 2: Edge Extraction for Content Zone** (`_extract_arc_edges`)

For content zone detection, ARCs are **flattened to actual geometry**:
```python
def _extract_arc_edges(entity: Any) -> list[LineString]:
    points = list(entity.flattening(sagitta=ARC_FLATTENING_SAGITTA))
    # Creates line segments along the actual arc path
```

The flattened arc only covers 270°-356°, so the leftmost x-coordinate is 0 (at the 270° start point), not -779.

**Step 3: Paint Bucket Region Detection**

- 99 polygons detected from unified edge geometry
- Leftmost polygon edge at x = -50 (from small LINE entities)

**Step 4: Min Area Filter (50,000 sq units)**

- Only 10 polygons survive
- Small polygons near x=-50 are filtered out
- Surviving polygons have min_x = 0

**Step 5: Content Zone Bounding Box**

Union bounding box of 10 surviving polygons:
```
cz_min_x = 0.00
cz_max_x = 3905.00
```

**Step 6: Trim Value Calculation**

```
trim_left = cz_min_x - block_min_x
         = 0.00 - (-779.00)
         = 779.00
```

### The 779 Value

The value 779 is:
- The **radius** of all 5 ARCs in the block
- The **horizontal distance** from the full-circle bbox left edge to the actual arc start point
- NOT the arc length (which is ~1170.57 for each 86° arc)

## Surviving Polygons After Filtering

| # | Net Area | X Range | Description |
|---|----------|---------|-------------|
| 1 | 3,466,927 | 0 - 3905 | Main content area (887.83 height) |
| 2-6 | ~382,421 each | Various | 5 door compartment regions (~769×658 each) |
| 7 | 285,305 | 0 - 3905 | Horizontal strip |
| 8-10 | ~62,871 each | Various | Upper edge strips |

All surviving polygons start at x ≥ 0, confirming the content zone min_x = 0.

## Related Tests

**Existing tests do NOT cover this specific scenario.** Current test coverage includes:

- `TestTrimValueCalculation` - Tests trim values for centered/offset content zones
- `TestCurvedFilterIntegration` - Tests curved polygon filtering
- Arc/circle edge extraction tests - Verify flattening produces correct geometry

**Missing test case**: Arc bbox discrepancy where block bbox uses full circle extents but content zone uses actual arc geometry.

## Recommendations

### Option 1: Accept Current Behavior (No Change)

The current behavior is **technically correct** given the design:
- Block bbox is documented as "simplified" for ARCs
- Content zone trim values accurately reflect the difference between the theoretical block extent and actual content

**Pros**: No code changes, maintains simplicity
**Cons**: May confuse users expecting trim values based on actual visible geometry

### Option 2: Use Accurate Arc Bounding Box

Modify `_get_block_bounding_box()` to calculate actual arc extents by checking which quadrant points fall within the arc's angular range.

**Pros**: More accurate block dimensions
**Cons**: More complex calculation, may break existing expectations

### Option 3: Add Documentation/Test Coverage

Add a test case that explicitly documents this behavior and ensures consistency.

```python
def test_arc_bbox_discrepancy_trim_values(self) -> None:
    """Verify trim values when ARCs create bbox vs content zone discrepancy.

    Block bbox uses full circle extents for ARCs (simplified).
    Content zone uses actual flattened arc geometry.
    This creates a discrepancy reflected in trim values.
    """
    # Test implementation...
```

## Next Steps

1. Decide whether this behavior is acceptable or needs modification
2. If acceptable, add test coverage to document the expected behavior
3. If modification needed, implement accurate arc bounding box calculation
