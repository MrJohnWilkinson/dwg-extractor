# Block Suggested Trim Right Calculation Analysis

## Executive Summary

The "Block Suggested Trim Right" value of `7292` is correctly calculated based on the **content zone detection algorithm** and the user's filter settings. The discrepancy between the calculated value (7292) and the user's expected value (content zone extending to X=13427) occurs because the polygon at X=13427 contains a **17-unit side segment** that fails the **Min Side Filter** threshold of 101.0.

## Table Summary

| Metric | Current Result | User Expectation | Difference |
|--------|---------------|------------------|------------|
| Block max_x | 14321.00 | 14321.00 | - |
| Content zone max_x | 7029.00 | 13427.00 | -6398.00 |
| **Suggested Trim Right** | **7292.00** | **894.00** | +6398.00 |
| Polygons surviving filters | 4 | 30+ | -26 |
| Polygon at X=13427 shortest side | 17.00 | - | Fails 101.0 filter |

## Relevant Files

- **app/core/geometry.py:1604-1876** - `_detect_content_zone()` function that calculates trim values
- **app/core/geometry.py:87-164** - `calculate_shortest_straight_side()` function that evaluates polygon side lengths
- **app/core/geometry.py:1852-1854** - Trim calculation formulas:
  ```python
  trim_left = round(cz_min_x - block_min_x, 2)
  trim_right = round(block_max_x - cz_max_x, 2)
  ```
- **app/core/extractor.py:1317-1331** - Where content zone detection is invoked with user settings

## Step-by-Step Calculation

### Step 1: Block Bounding Box Calculation

The block's bounding box is calculated from all LINE entities:

```
Block: Grocery_Gondola_Combined - 2000H  - 1240W _505_505_-80724766-GROUND FFL
Block bbox: (min_x=-1177.00, min_y=-620.00, max_x=14321.00, max_y=620.00)
Block dimensions: 15498.00 x 1240.00
```

### Step 2: Polygon Detection

Paint-bucket algorithm finds 351 closed regions/polygons from the block's 524 LINE entities.

### Step 3: Filter Application (User Settings)

With the user's settings:
- **Min Side Filter: 101.0** - Polygons with shortest side < 101 are removed
- **Min Area Filter: 80,000** - Polygons with net area < 80,000 are removed

```
Before filters: 351 polygons
After side filter (min_side=101): 30 polygons
After area filter (min_area=80000): 4 polygons
```

### Step 4: Surviving Polygons

Only 4 polygons pass both filters:

| Polygon | BBox X Range | BBox Y Range | Width | Height | Area | Shortest Side |
|---------|--------------|--------------|-------|--------|------|---------------|
| 1 | 3373 - 4287 | 35 - 540 | 914 | 505 | 461,570 | 505 |
| 2 | 6115 - 7029 | 35 - 540 | 914 | 505 | 461,570 | 505 |
| 3 | -283 - 631 | -540 - -35 | 914 | 505 | 461,570 | 505 |
| 4 | 2459 - 3373 | -540 - -35 | 914 | 505 | 461,570 | 505 |

### Step 5: Content Zone Calculation

The content zone is the union bounding box of all surviving polygons:

```
Content zone bbox: (min_x=-283.00, min_y=-540.00, max_x=7029.00, max_y=540.00)
```

### Step 6: Trim Value Calculation

```
trim_right = block_max_x - cz_max_x
trim_right = 14321.00 - 7029.00
trim_right = 7292.00
```

## Why Polygons at X=13427 Are Filtered Out

### The Polygon Structure

The polygons extending to X=13427 (Polygon indices 0 and 7 in the raw polygon list) have this vertex structure:

```
Polygon 0 vertices (17 points):
  (13427, 540) -> (13427, 35) -> (13410, 35) -> (12530, 35) -> (12513, 35) -> (12513, 540) -> ... back to start
```

### The 17-Unit Segment

Due to internal structure in the CAD drawing, there's a small horizontal segment at the bottom edge:

```
Side from (12530, 35) to (12513, 35) = 17.00 units
```

This creates a notch in what would otherwise be a clean rectangle:

```
                  ┌──────────────────────────────┐ Y=540
                  │                              │
                  │                              │
X=12513           │                              │ X=13427
      ┌───────────┤                              │
      │ 17 units  │◄─── Small notch             │ Y=35
      └───────────┼──────────────────────────────┘
            X=12530
```

### Filter Result

| Check | Value | Threshold | Result |
|-------|-------|-----------|--------|
| Area | 461,570 | 80,000 | PASS |
| Shortest Side | 17.00 | 101.0 | **FAIL** |

The polygon is **filtered out** because its shortest side (17 units) is less than the Min Side Filter threshold (101 units).

## Verification: Disabling Min Side Filter

When Min Side Filter is disabled (set to 0):

```
Content zone detected: True
Filtered polygon count: 30
Content zone max_x: 13427.00
Suggested trim right: 894.00
```

This confirms that with the filter disabled, the content zone extends to X=13427, producing the user's expected trim_right value of 894.

## Root Cause

The block geometry contains internal structural lines between X=12513 and X=12530 (specifically at Y=35 and Y=-35) that create small 17-unit segments within otherwise large polygons. These segments cause the polygon to fail the Min Side Filter.

### Source Lines Creating the 17-Unit Segment

```
Line: (12513, 35) -> (12530, 35)   [horizontal, 17 units] ← Creates the short side
Line: (12530, 35) -> (13410, 35)   [horizontal, 880 units]
Line: (12530, -35) -> (12530, 35)  [vertical, 70 units]
```

## Simple List Summary

- **Calculated trim_right (7292)** = block_max_x (14321) - content_zone_max_x (7029)
- **User's expected trim_right (894)** = block_max_x (14321) - 13427
- The polygon at X=13427 has a **17-unit side** that fails the **101-unit Min Side Filter**
- Only 4 of 351 polygons survive both filters (min side 101, min area 80000)
- The rightmost surviving polygon extends only to X=7029
- **Solution**: Lower the Min Side Filter value (e.g., to 15) to include polygons at X=13427
