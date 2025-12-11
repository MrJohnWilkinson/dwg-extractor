# Largest Polygon Selection Status After Net Area Filter Implementation

## Executive Summary

The net area filter implementation **did NOT remove** the "largest polygon" selection logic for Block Content Zone. The code still selects polygons with the **maximum net area** as the content zone winner. However, the key change is that "largest" now means **largest net area** (gross minus contained) rather than largest gross area, which correctly handles nested "picture frame" scenarios.

## Table Summary

| Aspect | Before Implementation | After Implementation | Status |
|--------|----------------------|---------------------|--------|
| Selection criteria | Max gross area | Max **net** area | ✅ Changed |
| Largest polygon wins | Yes | Yes | ✅ Preserved |
| Picture frame handling | Outer frame wins (incorrect) | Inner polygon wins (correct) | ✅ Fixed |
| Tie handling | Union bounding box | Union bounding box | ✅ Unchanged |
| Filter applies to | Gross area | Net area | ✅ Changed |

## Relevant Files

- **`app/core/geometry.py:1130-1150`** - Content zone selection logic uses `max_net_area` and `tied_shapes` to find the polygon(s) with largest net area
- **`app/core/geometry.py:926-980`** - `_calculate_net_areas()` calculates net area (gross minus contained) for each polygon
- **`app/core/geometry.py:1099-1116`** - Net area filtering applied after calculation

## Selection Logic Analysis

The content zone selection at `geometry.py:1130-1150` still operates on the principle of **"largest polygon wins"**:

```python
# Find maximum net area value (already sorted descending)
max_net_area = net_areas[0][1]

# Find all shapes tied for maximum net area
tied_shapes = [shape for shape, net_area in net_areas if net_area == max_net_area]
```

**Key observations:**
1. `_calculate_net_areas()` returns polygons sorted by net area descending
2. The first element `net_areas[0]` has the largest net area
3. All polygons tied for max net area are collected
4. Content zone bbox is calculated from winner(s)

## What Changed vs What Stayed Same

### Changed
- **Definition of "largest"**: Now uses net area (own area minus contained polygons) instead of gross area
- **Filter target**: `min_area_filter` now filters by net area, not gross area

### Stayed Same
- **Selection principle**: Largest area polygon(s) still win as content zone
- **Tie handling**: Multiple polygons with equal max area → union bounding box
- **Side filter**: Still uses gross geometry (shortest straight side)

## Practical Impact

| Scenario | Old Behavior | New Behavior |
|----------|-------------|--------------|
| Single rectangle | Selected (gross=net) | Selected (gross=net) |
| Picture frame (100x100 outer, 80x80 inner) | Outer wins (gross=10000) | Inner wins (net=6400 > outer net=3600) |
| Multiple equal areas | Union bbox | Union bbox |

## Recommendations

No recommendations - the implementation correctly preserves the "largest polygon wins" principle while fixing the definition of "largest" to use net area instead of gross area.

## Next Steps

None required - the implementation is complete and working as designed.
