# Trim Amount Calculation Breakdown

## Executive Summary
This report explains how trim values are calculated for each block in `sample-blocks.dxf`. The system uses a 6-step algorithm: calculate block bounding box, extract closed polygons (LWPOLYLINEs and LINE cycles), compute net areas (gross area minus contained polygon areas), identify the content zone (largest net area), then derive trim values from the difference between block and content zone bounding boxes.

## Table Summary

| Block Name | Width | Height | Polygons | Content Zone | trim_left | trim_right | trim_top | trim_bottom |
|------------|-------|--------|----------|--------------|-----------|------------|----------|-------------|
| GS900x450HGE_Liquor | 926.00 | 481.00 | 3 | 14,202.50 | **26.0** | **26.0** | **440.38** | **24.38** |
| AP #5-4 | 762.00 | 4876.80 | 1 | 3,716,121.60 | 0.0 | 0.0 | 0.0 | 0.0 |
| Bread gondola | 1219.20 | 1219.20 | 1 | 1,486,448.64 | 0.0 | 0.0 | 0.0 | 0.0 |
| Gcase(w1800) | 600.00 | 1800.00 | 1 | 1,080,000.00 | 0.0 | 0.0 | 0.0 | 0.0 |

## Relevant Files
- `app/core/geometry.py` - Contains all trim calculation functions (`_detect_content_zone`, `_calculate_net_areas`, `_get_polygon_bbox`, `_shoelace_area`)
- `app/core/extractor.py` - Orchestrates extraction and calls geometry functions (lines 908-925)
- `app/core/constants.py` - Performance thresholds (`POLYGON_COUNT_THRESHOLD=30`, `LINE_SEGMENT_THRESHOLD=200`)
- `app/tests/assets/samples/sample-blocks.dxf` - Test file analyzed

## Algorithm Overview (6 Steps)

### Step 1: Block Bounding Box
Calculate the overall extents of all entities in the block definition:
- Iterate through LINE, LWPOLYLINE, CIRCLE, ARC, POINT entities
- Track min/max X and Y coordinates
- Result: `(block_min_x, block_min_y, block_max_x, block_max_y)`

### Step 2: Extract Closed LWPOLYLINEs
Find closed polygon shapes from LWPOLYLINE entities:
- Filter for `entity.closed == True`
- Extract vertex coordinates as `[(x, y), ...]`
- Require minimum 3 vertices

### Step 3: Extract LINE Cycles
Find closed polygons formed by connected LINE segments:
- Build adjacency graph from LINE endpoints
- Use DFS to detect cycles (closed paths)
- Performance bounded by `LINE_SEGMENT_THRESHOLD` and timeout

### Step 4: Calculate Net Areas
For each polygon, compute: `net_area = gross_area - sum(contained_polygon_areas)`
- Gross area uses shoelace formula
- Containment checked via ray-casting algorithm
- Sorted by net area descending

### Step 5: Identify Content Zone
Select the polygon(s) with largest net area:
- If single winner: use its bounding box
- If tied: use union bounding box of all tied shapes
- Result: `(cz_min_x, cz_min_y, cz_max_x, cz_max_y)`

### Step 6: Calculate Trim Values
Derive trim amounts from difference between block bbox and content zone bbox:
```
trim_left   = cz_min_x - block_min_x
trim_right  = block_max_x - cz_max_x
trim_top    = block_max_y - cz_max_y
trim_bottom = cz_min_y - block_min_y
```

---

## Block 1: GS900x450HGE_Liquor (Non-Zero Trims)

### Step 1: Block Bounding Box
```
Block bbox: min_x=0.00, min_y=0.00, max_x=926.00, max_y=481.00
Block dimensions: width=926.00, height=481.00
```

### Step 2: Extract Closed LWPOLYLINEs
Found **3 closed LWPOLYLINE(s)**:
| Shape | Vertices | Area | Bounding Box |
|-------|----------|------|--------------|
| 1 | 4 | 1,690.00 | (0.00, 0.00, 26.00, 65.00) |
| 2 | 4 | 1,690.00 | (900.00, 0.00, 926.00, 65.00) |
| 3 | 4 | 14,202.50 | (26.00, 24.38, 900.00, 40.62) |

### Step 3: Extract LINE Cycles
Found **0 LINE cycle(s)**

### Step 4: Calculate Net Areas
```
Total polygons: 3
Net areas (sorted descending):
  #1: gross=14,202.50, net=14,202.50  <-- LARGEST
  #2: gross=1,690.00, net=1,690.00
  #3: gross=1,690.00, net=1,690.00
```
Note: No containment relationships, so net = gross for all shapes.

### Step 5: Identify Content Zone
```
Maximum net area: 14,202.50
Shapes tied for max: 1
Content zone bbox: (26.00, 24.38, 900.00, 40.62)
```

### Step 6: Calculate Trim Values
```
trim_left   = cz_min_x - block_min_x = 26.00 - 0.00 = 26.0
trim_right  = block_max_x - cz_max_x = 926.00 - 900.00 = 26.0
trim_top    = block_max_y - cz_max_y = 481.00 - 40.62 = 440.38
trim_bottom = cz_min_y - block_min_y = 24.38 - 0.00 = 24.38
```

**Interpretation:** The content zone is a narrow horizontal strip (Shape 3) near the bottom of the block. The two small rectangles at the corners (Shapes 1 & 2) are excluded. Large trim_top (440.38) indicates most of the block height is outside the content zone.

---

## Block 2: AP #5-4 (Zero Trims)

### Step 1: Block Bounding Box
```
Block bbox: min_x=0.00, min_y=0.00, max_x=762.00, max_y=4876.80
Block dimensions: width=762.00, height=4876.80
```

### Step 2: Extract Closed LWPOLYLINEs
Found **1 closed LWPOLYLINE(s)**:
| Shape | Vertices | Area | Bounding Box |
|-------|----------|------|--------------|
| 1 | 4 | 3,716,121.60 | (0.00, 0.00, 762.00, 4876.80) |

### Step 3-4: Net Areas
```
Total polygons: 1
Net area: 3,716,121.60 (no other shapes to subtract)
```

### Step 5: Content Zone
```
Content zone bbox: (0.00, 0.00, 762.00, 4876.80)
```
The single polygon spans the entire block.

### Step 6: Calculate Trim Values
```
trim_left   = 0.00 - 0.00 = 0.0
trim_right  = 762.00 - 762.00 = 0.0
trim_top    = 4876.80 - 4876.80 = 0.0
trim_bottom = 0.00 - 0.00 = 0.0
```

**Interpretation:** Content zone equals block bounds. No trimming needed.

---

## Block 3: Bread gondola (Zero Trims)

### Step 1: Block Bounding Box
```
Block bbox: min_x=0.00, min_y=0.00, max_x=1219.20, max_y=1219.20
Block dimensions: width=1219.20, height=1219.20
```

### Step 2: Extract Closed LWPOLYLINEs
Found **1 closed LWPOLYLINE(s)**:
| Shape | Vertices | Area | Bounding Box |
|-------|----------|------|--------------|
| 1 | 4 | 1,486,448.64 | (0.00, 0.00, 1219.20, 1219.20) |

### Step 3-4: Net Areas
```
Total polygons: 1
Net area: 1,486,448.64
```

### Step 5: Content Zone
```
Content zone bbox: (0.00, 0.00, 1219.20, 1219.20)
```

### Step 6: Calculate Trim Values
```
All trim values = 0.0
```

**Interpretation:** Single polygon fills entire block bounds.

---

## Block 4: Gcase(w1800) (Zero Trims)

### Step 1: Block Bounding Box
```
Block bbox: min_x=0.00, min_y=0.00, max_x=600.00, max_y=1800.00
Block dimensions: width=600.00, height=1800.00
```

### Step 2: Extract Closed LWPOLYLINEs
Found **1 closed LWPOLYLINE(s)**:
| Shape | Vertices | Area | Bounding Box |
|-------|----------|------|--------------|
| 1 | 4 | 1,080,000.00 | (0.00, 0.00, 600.00, 1800.00) |

### Step 3-4: Net Areas
```
Total polygons: 1
Net area: 1,080,000.00
```

### Step 5: Content Zone
```
Content zone bbox: (0.00, 0.00, 600.00, 1800.00)
```

### Step 6: Calculate Trim Values
```
All trim values = 0.0
```

**Interpretation:** Single polygon fills entire block bounds.

---

## Key Formulas Reference

### Shoelace Formula (Area Calculation)
```python
area = abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(n))) / 2
```

### Point-in-Polygon (Ray Casting)
Cast horizontal ray from point, count edge crossings. Odd = inside.

### Trim Value Formulas
```
trim_left   = content_zone_min_x - block_min_x
trim_right  = block_max_x - content_zone_max_x
trim_top    = block_max_y - content_zone_max_y
trim_bottom = content_zone_min_y - block_min_y
```

## Recommendations
1. Blocks with **zero trims** have a single outer polygon matching block bounds - no internal "content zone" differentiation
2. Blocks with **non-zero trims** (like GS900x450HGE_Liquor) have multiple shapes where the largest-area shape defines the content zone
3. The algorithm correctly identifies the "main" shape when decorative elements exist at block edges
