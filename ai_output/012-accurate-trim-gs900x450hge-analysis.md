# Accurate Trimming for GS900x450HGE_Liquor Block

## Executive Summary
The current content zone detection algorithm incorrectly identifies the narrow horizontal LWPOLYLINE (area=14,202) as the content zone, yielding trims of 26/26/440/24. The user's expected trims (13/13/0/24.375) require detecting the composite visual boundary formed by 3 structural LINE entities combined with LWPOLYLINE shapes. Several algorithmic approaches can achieve this, with the "Structural LINE + Largest LWPOLY Union" approach offering the best balance of accuracy and complexity.

## Table Summary

| Approach | trim_left | trim_right | trim_top | trim_bottom | Complexity | Accuracy |
|----------|-----------|------------|----------|-------------|------------|----------|
| **Expected** | **13** | **13** | **0** | **24.375** | N/A | Target |
| Current (Largest LWPOLY) | 26 | 26 | 440.38 | 24.38 | O(n³) | Poor |
| All LINE Bbox | 13 | 13 | 0 | 0 | O(n) | Partial |
| Structural LINE Bbox | 13 | 13 | 0 | 416 | O(n) | Partial |
| **LINE + Largest LWPOLY Union** | **13** | **13** | **0** | **24.38** | O(n²) | **Excellent** |
| Mixed Entity Cycle Detection | ~13 | ~13 | ~0 | ~24 | O(n!) | High Risk |
| Convex Hull | 0 | 0 | 0 | 0 | O(n log n) | Poor |

## Relevant Files
- `app/core/geometry.py:737-847` - `_detect_content_zone()` current implementation
- `app/core/geometry.py:359-388` - `_extract_closed_lwpolylines()` extracts closed LWPOLYLINE shapes
- `app/core/geometry.py:547-673` - `_extract_line_cycles()` extracts LINE-only cycles
- `app/core/constants.py:136-148` - Performance thresholds
- `app/tests/assets/samples/sample-blocks.dxf` - Test file containing GS900x450HGE_Liquor block
- `ai_output/010-trim-calculation-breakdown.md` - Previous trim analysis
- `ai_output/011-line-cycle-detection-analysis.md` - LINE cycle detection limitations

## Block Geometry Analysis

### Entity Inventory
```
Block: GS900x450HGE_Liquor
Block bbox: (0, 0) to (926, 481)
Block dimensions: 926 x 481

LINE entities (4):
  LINE 1: (13, 481) -> (913, 481)     # Top horizontal edge
  LINE 2: (13, 481) -> (13, 65)       # Left vertical edge
  LINE 3: (913, 65) -> (913, 481)     # Right vertical edge
  LINE 4: (26, 0) -> (900, 0)         # Baseline (decorative)

LWPOLYLINE entities (3):
  POLY 1: (0, 0) to (26, 65)          # Bottom-left corner rectangle
  POLY 2: (900, 0) to (926, 65)       # Bottom-right corner rectangle
  POLY 3: (26, 24.38) to (900, 40.62) # Middle connector strip (largest area)
```

### Visual Structure Description
The user describes an 8-sided primary polygon formed by:
1. **Top edge**: LINE 1 (horizontal at y=481)
2. **Left edge**: LINE 2 (vertical at x=13)
3. **Bottom-left step**: Connects to POLY 1
4. **Bottom edge**: Uses top edge of POLY 3 (at y=40.62)
5. **Bottom-right step**: Connects to POLY 2
6. **Right edge**: LINE 3 (vertical at x=913)

### Why Current Algorithm Fails
The current algorithm:
1. Extracts 3 closed LWPOLYLINEs (POLY 1, 2, 3)
2. Finds no LINE cycles (LINEs don't form closed loop alone)
3. Selects POLY 3 as content zone (largest net area = 14,202)
4. Returns bbox of POLY 3: (26, 24.38, 900, 40.62)

**Result**: trim_left=26, trim_right=26, trim_top=440.38, trim_bottom=24.38

**Problem**: Algorithm cannot detect composite shapes formed by mixed entity types.

---

## Approach Analysis

### Approach 1: Mixed Entity Cycle Detection (Not Recommended)

**Concept**: Build unified adjacency graph from both LINE endpoints and LWPOLYLINE vertices, then run DFS to find cycles.

**Implementation**:
```python
# Pseudocode
graph = build_adjacency_graph(lines + lwpolyline_segments)
cycles = dfs_find_cycles(graph)
content_zone = largest_cycle_by_net_area(cycles)
```

**Challenges**:
- LINEs and LWPOLYLINEs don't share exact endpoints (LINE at x=13, POLY at x=26)
- Would require tolerance-based endpoint matching
- DFS complexity explodes with combined graph: O(n!) worst case
- No topological connectivity in GS900x450HGE_Liquor block

**Verdict**: Not viable for this block - entities aren't topologically connected.

---

### Approach 2: LINE Bounding Box (Partial Solution)

**Concept**: Use bounding box of all LINE entities as content zone.

**Implementation**:
```python
line_points = []
for entity in block_def:
    if entity.dxftype() == 'LINE':
        line_points.extend([entity.dxf.start, entity.dxf.end])
content_zone = bounding_box(line_points)
```

**Results for GS900x450HGE_Liquor**:
```
LINE bbox: (13, 0) to (913, 481)  # Includes baseline LINE 4 at y=0
Trims: left=13, right=13, top=0, bottom=0
```

**Problem**: LINE 4 at y=0 pulls the bottom boundary down. Expected bottom=24.375, got bottom=0.

---

### Approach 3: Structural LINE Bounding Box (Better)

**Concept**: Filter out "baseline" LINEs (those at block boundary y=0) and use remaining structural LINEs.

**Implementation**:
```python
structural_lines = [l for l in lines if not is_baseline(l)]
content_zone = bounding_box(structural_line_points)

def is_baseline(line):
    return abs(line.start.y) < tolerance and abs(line.end.y) < tolerance
```

**Results for GS900x450HGE_Liquor**:
```
Structural LINEs: LINE 1, LINE 2, LINE 3 (excluding LINE 4)
Structural LINE bbox: (13, 65) to (913, 481)
Trims: left=13, right=13, top=0, bottom=416
```

**Problem**: Gets left/right/top correct but bottom is wrong (65 instead of 24.375).

---

### Approach 4: LINE + Largest LWPOLY Union (Recommended)

**Concept**: Combine structural LINE bounding box with largest LWPOLYLINE to capture the full visual boundary.

**Algorithm**:
1. Calculate structural LINE bounding box (excluding baselines)
2. Find LWPOLYLINE with largest area
3. Take union of both bounding boxes
4. Use min_y from largest LWPOLY if below LINE min_y

**Implementation**:
```python
def detect_content_zone_v2(block_def, block_bbox):
    # Step 1: Get structural LINE bbox
    structural_lines = filter_structural_lines(block_def)
    line_bbox = bounding_box(structural_lines)

    # Step 2: Get largest LWPOLYLINE
    lwpolys = extract_closed_lwpolylines(block_def)
    largest_lwpoly = max(lwpolys, key=shoelace_area)
    lwpoly_bbox = bounding_box(largest_lwpoly)

    # Step 3: Union bboxes with preference for LINE x-bounds
    cz_min_x = min(line_bbox.min_x, lwpoly_bbox.min_x)
    cz_max_x = max(line_bbox.max_x, lwpoly_bbox.max_x)
    cz_min_y = min(line_bbox.min_y, lwpoly_bbox.min_y)
    cz_max_y = max(line_bbox.max_y, lwpoly_bbox.max_y)

    return (cz_min_x, cz_min_y, cz_max_x, cz_max_y)
```

**Results for GS900x450HGE_Liquor**:
```
Structural LINE bbox: (13, 65) to (913, 481)
Largest LWPOLY bbox (POLY 3): (26, 24.38) to (900, 40.62)
Union: min_x=min(13,26)=13, max_x=max(913,900)=913
       min_y=min(65,24.38)=24.38, max_y=max(481,40.62)=481
Content zone: (13, 24.38) to (913, 481)
Trims: left=13, right=13, top=0, bottom=24.38
```

**Accuracy**: Matches expected values exactly (24.38 ≈ 24.375).

---

### Approach 5: Convex Hull (Not Suitable)

**Concept**: Calculate convex hull of all entity vertices.

**Problem**: The GS900x450HGE_Liquor 8-sided polygon is concave. Convex hull would include the corner rectangles, giving trims of 0/0/0/0.

**Verdict**: Not suitable for concave content zones.

---

### Approach 6: Weighted Area Voting (Alternative)

**Concept**: Weight entity contributions by their area when calculating content zone.

**Implementation**:
```python
# Give LINE bbox higher weight if structural LINEs span significant area
line_area = (line_max_x - line_min_x) * (line_max_y - line_min_y)
poly_areas = [shoelace_area(p) for p in lwpolys]
total_area = line_area + sum(poly_areas)

# Weighted centroid/bounds calculation
```

**Verdict**: More complex, may not improve accuracy for this case.

---

### Approach 7: Heuristic Edge Classification (Most Flexible)

**Concept**: Classify entities as "structural" vs "decorative" based on heuristics.

**Heuristics**:
1. **Position**: Entities at block boundary edges (x=0, y=0, x=max, y=max) may be decorative
2. **Size**: Small rectangles relative to block size are likely decorative
3. **Aspect ratio**: Very narrow shapes may be trim guides
4. **Connection**: Entities not connected to larger shapes may be decorative

**Implementation**:
```python
def classify_entity(entity, block_bbox):
    if is_at_boundary(entity, block_bbox):
        return 'decorative'
    if relative_area(entity, block_bbox) < 0.05:
        return 'decorative'
    return 'structural'

structural_entities = [e for e in entities if classify_entity(e) == 'structural']
content_zone = bounding_box(structural_entities)
```

**Verdict**: Flexible but requires tuning thresholds for different block types.

---

## Recommendations

### Primary Recommendation: Approach 4 (LINE + Largest LWPOLY Union)

Implement a hybrid approach that combines:
1. Structural LINE bounding box (excluding baselines)
2. Union with largest-area LWPOLYLINE bounding box

**Rationale**:
- Achieves expected trim values for GS900x450HGE_Liquor
- O(n²) complexity (acceptable)
- Leverages existing extraction functions
- Works for blocks with mixed LINE + LWPOLYLINE visual boundaries

### Implementation Steps

1. **Add baseline detection function**:
   ```python
   def _is_baseline_line(entity, block_bbox, tolerance=0.01):
       """Check if LINE is at block boundary (decorative baseline)."""
       start_y, end_y = entity.dxf.start.y, entity.dxf.end.y
       at_bottom = abs(start_y - block_bbox[1]) < tolerance and abs(end_y - block_bbox[1]) < tolerance
       at_top = abs(start_y - block_bbox[3]) < tolerance and abs(end_y - block_bbox[3]) < tolerance
       return at_bottom or at_top
   ```

2. **Add structural LINE bbox function**:
   ```python
   def _get_structural_line_bbox(block_def, block_bbox):
       """Get bounding box of structural (non-baseline) LINEs."""
       points = []
       for entity in block_def:
           if entity.dxftype() == 'LINE' and not _is_baseline_line(entity, block_bbox):
               points.extend([entity.dxf.start, entity.dxf.end])
       return _calculate_bbox(points) if points else None
   ```

3. **Modify `_detect_content_zone()` to use hybrid approach**:
   ```python
   # In _detect_content_zone():
   line_bbox = _get_structural_line_bbox(block_def, block_bbox)
   if line_bbox and lwpolys:
       largest_lwpoly_bbox = _get_polygon_bbox(max(lwpolys, key=_shoelace_area))
       content_bbox = union_bbox(line_bbox, largest_lwpoly_bbox)
   ```

### Alternative: Configuration Flag

Add a configuration option to select content zone detection strategy:

```python
CONTENT_ZONE_STRATEGY = 'hybrid'  # Options: 'lwpoly_only', 'line_only', 'hybrid', 'union_all'
```

This allows users or downstream code to select the appropriate strategy for different block types.

## Next Steps

1. **Validate approach** on other blocks in sample-blocks.dxf (AP #5-4, Bread gondola, Gcase)
2. **Create test cases** for hybrid detection approach
3. **Implement** `_get_structural_line_bbox()` and `_is_baseline_line()` functions
4. **Add configuration flag** for detection strategy selection
5. **Update documentation** in geometry.py module docstring

## Appendix: Raw Geometry Data

### GS900x450HGE_Liquor Entity Coordinates
```
LINE 1: (13.00, 481.00) -> (913.00, 481.00)  [TOP EDGE]
LINE 2: (13.00, 481.00) -> (13.00, 65.00)    [LEFT EDGE]
LINE 3: (913.00, 65.00) -> (913.00, 481.00)  [RIGHT EDGE]
LINE 4: (26.00, 0.00) -> (900.00, 0.00)      [BASELINE - decorative]

POLY 1: (0,0)-(26,0)-(26,65)-(0,65) closed   [BOTTOM-LEFT CORNER]
POLY 2: (900,0)-(926,0)-(926,65)-(900,65)    [BOTTOM-RIGHT CORNER]
POLY 3: (26,24.38)-(900,24.38)-(900,40.62)-(26,40.62) [CONNECTOR]
```

### Calculation Verification
```
Block bbox: (0, 0, 926, 481)
Expected content zone: (13, 24.375, 913, 481)

trim_left   = 13 - 0 = 13       ✓
trim_right  = 926 - 913 = 13    ✓
trim_top    = 481 - 481 = 0     ✓
trim_bottom = 24.375 - 0 = 24.375 ✓
```
