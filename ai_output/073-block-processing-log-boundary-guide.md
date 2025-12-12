# Block Processing Log Boundary Guide

## Executive Summary
The DXF Block Extractor processes blocks sequentially, with each block's processing bounded by explicit START and END log markers. Every block is wrapped with `[BLOCK START] 'BlockName'` at the beginning and `[BLOCK END] 'BlockName' (X.XXXs)` at the end, making it easy to parse logs programmatically and identify block boundaries.

## Table Summary

| Log Pattern | Level | Meaning | Location |
|-------------|-------|---------|----------|
| `[BLOCK START] 'BlockName'` | INFO | **Block processing START** | extractor.py:1232 |
| `[BLOCK END] 'BlockName' (X.XXXs)` | INFO | **Block processing END** (always) | extractor.py:1301 |
| `[BlockName] Detecting content zone...` | INFO | Content zone detection phase begins | geometry.py:1142 |
| `Bounding box: processing entity type X` | DEBUG | Entity iteration within block | geometry.py:~210 |
| `Bounding box result: (...)` | DEBUG | Bounding box calculation complete | geometry.py:~290 |
| `Intersection points: X x-coords, Y y-coords` | DEBUG | Geometry analysis step | geometry.py |
| `Calculate segments: N points -> M segments` | DEBUG | Segment calculation step | geometry.py |
| `Extracted N edges from block` | DEBUG | Edge extraction complete | geometry.py |
| `Applied gap bridge snap: tolerance=X` | DEBUG | Snap tolerance applied | geometry.py |
| `Found N paint-bucket regions` | DEBUG | Region detection complete | geometry.py:1184 |
| `[BlockName] Paint bucket regions: Xs (N polygons)` | INFO | Slow region detection (>0.5s) | geometry.py:1180 |
| `[BlockName] Side filter: X -> Y polygons` | DEBUG | Polygon filtering step | geometry.py:1196 |
| `Calculated net areas for N polygons` | DEBUG | Net area calculation complete | geometry.py |
| `[BlockName] Content zone detected: WxH` | INFO | Successful detection | geometry.py |
| `[BlockName] No closed shapes found` | DEBUG | No content zone found | geometry.py:1205 |

## Relevant Files

- **app/core/extractor.py** - Main extraction loop (lines 1207-1303): Iterates through block definitions, calls geometry functions, logs timing
- **app/core/geometry.py** - Content zone detection (lines 1050-1340): `_detect_content_zone()` function that produces most DEBUG logs
- **app/core/logger.py** - Logger setup: Configures the logging format with timestamps

## Block Processing Lifecycle

### Start Marker (Always Present)
```
14:06:24.940 [INFO] [BLOCK START] 'Stockroom_Hook_SafetyVestRail - Type 1-21011562-GROUND FFL'
```
This INFO-level message marks the **definitive start** of a block's processing.

### Processing Phase (DEBUG Messages)
Between start and end, you'll see DEBUG messages in this order:

1. **Edge Extraction**
   ```
   [DEBUG] Extracted 1154 edges from block
   ```

2. **Snapping**
   ```
   [DEBUG] Applied gap bridge snap: tolerance=3.0
   [DEBUG] Edge snapping: 1.15s  (only if slow)
   ```

3. **Region Detection**
   ```
   [DEBUG] Unary union: 27.85s  (only if slow)
   [DEBUG] Found 135 paint-bucket regions
   ```

4. **Filtering**
   ```
   [DEBUG] [BlockName] Side filter: 135 -> 0 polygons (min_side=10.0)
   ```

5. **Result**
   ```
   [DEBUG] [BlockName] No closed shapes found
   ```
   OR
   ```
   [DEBUG] Calculated net areas for N polygons, largest net area: X
   [INFO] [BlockName] Content zone detected: WxH
   ```

### End Marker (Always Present)
```
14:06:53.976 [INFO] [BLOCK END] 'Stockroom_Hook_SafetyVestRail - Type 1-21011562-GROUND FFL' (29.036s)
```
This INFO-level message marks the **definitive end** of a block's processing, including timing with millisecond precision.

## How to Parse Block Boundaries

### Method 1: Use Explicit START/END Markers
```python
import re

# Block start pattern
start_pattern = r"\[BLOCK START\] '(.+)'"
if match := re.search(start_pattern, line):
    block_name = match.group(1)

# Block end pattern with timing
end_pattern = r"\[BLOCK END\] '(.+)' \((\d+\.\d+)s\)"
if match := re.search(end_pattern, line):
    block_name = match.group(1)
    duration_seconds = float(match.group(2))
```

### Method 2: Simple Grep
```bash
# Extract all block boundaries with timing
grep "\[BLOCK" output.log
```
Output:
```
[BLOCK START] 'BlockA'
[BLOCK END] 'BlockA' (0.002s)
[BLOCK START] 'BlockB'
[BLOCK END] 'BlockB' (77.342s)
```

## Example: Identifying Block Boundaries in Your Log

Example log output:
```
14:06:24.920 [INFO] [BLOCK START] 'Parking_GuardRailBarrier - Type 1-80820042-GROUND FFL'
14:06:24.924 [DEBUG] Bounding box: processing entity type LINE
...
14:06:24.942 [INFO] [BLOCK END] 'Parking_GuardRailBarrier - Type 1-80820042-GROUND FFL' (0.022s)
14:06:24.942 [INFO] [BLOCK START] 'Stockroom_Hook_SafetyVestRail - Type 1-21011562-GROUND FFL'
14:06:24.943 [DEBUG] Bounding box: processing entity type LINE
...
14:06:53.976 [INFO] [BLOCK END] 'Stockroom_Hook_SafetyVestRail - Type 1-21011562-GROUND FFL' (29.034s)
```

| Block Name | Duration |
|------------|----------|
| `Parking_GuardRailBarrier - Type 1-80820042-GROUND FFL` | 0.022s |
| `Stockroom_Hook_SafetyVestRail - Type 1-21011562-GROUND FFL` | 29.034s |
| `Stockroom_SafetyCone - Stock_SafetyCone-24779600-GROUND FFL` | 0.002s |

## Recommendations

1. **Use `grep "\[BLOCK"` to extract boundaries** - Simple and effective for timing analysis
2. **Use the block name prefix** - Messages prefixed with `[BlockName]` belong to that block's content zone detection phase
3. **Millisecond precision** - All blocks now report timing with 3 decimal places for accurate profiling
4. **Entity type DEBUG messages without prefix** - These are bounding box calculations within the current block
