# Block R23-0103 Trim Bottom 782.27 Calculation Analysis

## Executive Summary
The "Block Suggested Trim Bottom" value of `782.27` differs from the expected `781` by exactly `1.27` units. This discrepancy is caused by an ARC entity that extends the block's bounding box bottom edge beyond the rectangular LWPOLYLINE geometry. The "Skip Curved Entities" setting only affects content zone polygon detection, not the block bounding box calculation, creating an asymmetry.

## Table Summary

| Component | Y-Coordinate | Source |
|-----------|--------------|--------|
| Block min_y (current) | 11664.6627 | ARC bottom extent |
| Block min_y (expected) | 11665.9365 | LWPOLYLINE bottom edge |
| Content zone min_y | 12446.9365 | Surviving polygon union |
| **Trim Bottom (calculated)** | **782.27** | 12446.9365 - 11664.6627 |
| **Trim Bottom (expected)** | **781.00** | 12446.9365 - 11665.9365 |
| **Discrepancy** | **1.27** | Arc extends 1.27 below LWPOLYLINE |

## Relevant Files
- `app/core/geometry.py:332-521` - `_get_block_bounding_box()` includes ARCs in bounding box
- `app/core/geometry.py:1604-1877` - `_detect_content_zone()` respects skip_curved_entities for polygons
- `app/core/geometry.py:1068-1156` - `_extract_all_edges()` skips curves when skip_curved_entities=True
- `app/core/geometry.py:179-259` - `_get_arc_bounding_box()` calculates accurate arc extents

## Calculation Step-by-Step

### Step 1: Block Bounding Box Calculation
The block's bounding box is calculated by `_get_block_bounding_box()`:

```
Block entities:
- 3 ARCs (curved elements)
- 19 LWPOLYLINEs (rectangular content)
- 5 LINEs
- 12 ATTDEFs, 2 MTEXTs (text elements)
```

The **lowest Y-coordinate** comes from:
- **ARC**: center_y=12403.57, radius=738.91, angles=176.6-273.4 → bottom extent = **11664.6627**
- LWPOLYLINE: 3 vertices with min_y = 11665.9365

Since the ARC extends lower, `block_min_y = 11664.6627`.

### Step 2: Content Zone Detection
With user settings `Skip Curved Entities: Yes`, the polygon extraction:
1. Extracts 14 polygons from LINEs and LWPOLYLINEs (ARCs excluded)
2. Applies min_area_filter=100000 → 5 polygons survive
3. Calculates union bounding box of survivors → `cz_min_y = 12446.9365`

### Step 3: Trim Bottom Formula
```
trim_bottom = round(cz_min_y - block_min_y, 2)
            = round(12446.9365 - 11664.6627, 2)
            = round(782.2738, 2)
            = 782.27
```

## Root Cause

**Asymmetry in "Skip Curved Entities" application:**

| Calculation | Includes ARCs? |
|-------------|----------------|
| Block bounding box | Yes (always) |
| Content zone polygons | No (when Skip Curved Entities=Yes) |

The block's bottom edge is defined by an ARC that extends 1.27 units below the LWPOLYLINE geometry. When curved entities are skipped for content zone detection, the content zone is based only on rectangular geometry, but the block bounding box still includes the arc's full extent.

## Visual Explanation

```
                    Block Bounding Box
                         │
    ┌────────────────────┴────────────────────┐  ← block_max_y = 13506.94
    │                                          │
    │   ┌──────────────────────────────────┐  │  ← cz_max_y = 13506.94
    │   │                                  │  │
    │   │     Content Zone (polygons)      │  │
    │   │                                  │  │
    │   │                                  │  │
    │   └──────────────────────────────────┘  │  ← cz_min_y = 12446.94
    │              trim_bottom = 782.27       │      (polygon edge)
    │                    │                    │
    │  ╭──────╮   ARC extends here   ╭──────╮ │
    │  │      │          │           │      │ │  ← LWPOLYLINE min_y = 11665.94
    │  ╰──────╯          ▼           ╰──────╯ │
    └────────────────────────────────────────-┘  ← block_min_y = 11664.66 (ARC)
                         ↑
              ARC bottom extent (1.27 lower)
```

## Potential Solutions

1. **Respect skip_curved_entities in block bbox calculation** - Make `_get_block_bounding_box()` also skip curved entities when the setting is enabled
2. **Document the behavior** - Clarify that trim values are relative to full block extents including all geometry
3. **Add separate "trim source" option** - Allow user to choose whether trim is calculated from full bbox or non-curved bbox

## Simple List Summary

- Trim bottom = content zone min_y (12446.94) minus block min_y (11664.66) = **782.27**
- Block min_y is defined by an **ARC entity** that extends 1.27 units below the LWPOLYLINE geometry
- User sees 781 in block editor because they're viewing the **rectangular LWPOLYLINE boundary**, not the arc extent
- "Skip Curved Entities" only affects **polygon detection**, not **block bounding box calculation**
- The 1.27 discrepancy is the exact distance the arc's bottom extends below the LWPOLYLINE
