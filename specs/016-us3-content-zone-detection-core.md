# Feature: Content Zone Detection Core (US-3)

## Feature Description
Implement the core content zone detection algorithm that automatically identifies the primary "content zone" shape within a DXF block definition. The content zone is determined by finding the closed polygon with the largest net area (own area minus contained areas). This enables automatic derivation of trim values, reducing manual data entry for block analysis.

The implementation includes:
- Closed polygon detection from LWPOLYLINE entities (always fast)
- Closed polygon detection from LINE segments via cycle detection DFS
- Performance safeguards: LINE segment threshold, polygon count threshold, cycle detection timeout
- Area calculation using the shoelace formula
- Containment relationship detection using point-in-polygon algorithm
- Net area calculation (O(n^3) bounded by threshold)
- Trim value derivation from content zone bounding box relative to block bounding box

## User Story
As a DXF block analyzer
I want to automatically identify the "content zone" shape within a block definition
So that I can derive trim values and reduce manual data entry

## Problem Statement
Currently, determining the content zone of a block requires manual inspection. Blocks can contain multiple nested shapes (rectangles, chamfered corners, etc.) formed by either LWPOLYLINE entities or connected LINE segments. The content zone is typically the innermost significant shape, which should be automatically identified to calculate trim values for the block.

Complex blocks can cause performance issues:
- LINE cycle detection via DFS can hang on blocks with many LINE segments (967 segments caused 6+ minute hang)
- Net area calculation is O(n^3) and 102 polygons resulted in 140+ seconds processing time
- Without timeouts, the algorithm can hang indefinitely

## Solution Statement
Implement a multi-layered approach with performance safeguards:

1. **LWPOLYLINE Extraction**: Extract closed polygons from LWPOLYLINE entities (always fast, O(n) where n = entity count)

2. **LINE Cycle Detection**: Use DFS to find closed cycles from connected LINE segments with:
   - Pre-check: Skip if segment count > LINE_SEGMENT_THRESHOLD (200)
   - Timeout: Abort after CYCLE_DETECTION_TIMEOUT_SECONDS (5.0)
   - Abort checkpoints: Check abort_event every 1000 iterations

3. **Net Area Calculation**: For each polygon, calculate area minus areas of contained polygons with:
   - Pre-check: Skip if polygon count > POLYGON_COUNT_THRESHOLD (30)
   - Abort checkpoints: Check abort_event every 10 polygons

4. **Content Zone Selection**: Select the polygon with the largest net area

5. **Trim Value Derivation**: Calculate trim values from content zone bbox relative to block bbox

## Relevant Files
Use these files to implement the feature:

- `app/core/geometry.py` - Main implementation file for all content zone detection functions. Contains existing geometric utilities (_get_block_bounding_box, _categorize_rotation, etc.). New functions will be added here.
- `app/core/types.py` - TypedDict definitions for data structures. Will add Polygon type alias and ContentZoneData TypedDict.
- `app/core/constants.py` - Already contains POLYGON_COUNT_THRESHOLD, LINE_SEGMENT_THRESHOLD, CYCLE_DETECTION_TIMEOUT_SECONDS constants.
- `app/core/logger.py` - Logging utilities including setup_logger() for debug logging.
- `app/tests/core/test_geometry.py` - Existing geometry tests. New content zone tests will be added to a separate file.

### New Files
- `app/tests/core/test_content_zone.py` - Dedicated test file for content zone detection functionality.
- `app/tests/assets/create_content_zone_test.py` - Script to generate content zone test DXF file.
- `app/tests/assets/content_zone_test.dxf` - Test DXF with nested rectangles, chamfered shapes, mixed shapes.
- `app/tests/assets/create_many_lines_test.py` - Script to generate many lines test DXF file.
- `app/tests/assets/many_lines_test.dxf` - Test DXF with 500+ LINE segments for threshold testing.

## Implementation Plan
### Phase 1: Foundation
Add data types to `app/core/types.py`:
- Add `Polygon` type alias: `list[tuple[float, float]]`
- Add `ContentZoneData` TypedDict with suggested trim fields and content_zone_detected boolean

### Phase 2: Core Implementation
Add geometry functions to `app/core/geometry.py`:
1. Helper functions:
   - `_empty_content_zone_data()` - Returns empty ContentZoneData
   - `_count_line_segments()` - Counts LINE entities in block
   - `_extract_closed_lwpolylines()` - Extracts closed LWPOLYLINE polygons
   - `_shoelace_area()` - Calculates polygon area using shoelace formula
   - `_point_in_polygon()` - Ray-casting point-in-polygon test
   - `_polygon_contains_polygon()` - Tests if one polygon contains another
   - `_get_polygon_bbox()` - Gets bounding box of polygon vertices

2. Core algorithm functions:
   - `_extract_line_cycles()` - DFS cycle detection with timeout
   - `_calculate_net_areas()` - Net area calculation with abort checkpoints
   - `_detect_content_zone()` - Main orchestration function

3. Add `GeometryAbortedError` exception class for abort signaling

### Phase 3: Integration
Create test assets and comprehensive test suite:
- Create DXF test files with various scenarios
- Write unit tests for each function
- Write integration tests for full content zone detection

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Data Types to types.py
- Add `Polygon` type alias after existing imports: `Polygon = list[tuple[float, float]]`
- Add docstring explaining it represents a list of (x, y) vertices forming a closed polygon
- Add `ContentZoneData` TypedDict with fields:
  - `suggested_trim_left: float | None`
  - `suggested_trim_right: float | None`
  - `suggested_trim_top: float | None`
  - `suggested_trim_bottom: float | None`
  - `content_zone_detected: bool`
- Add comprehensive docstring for ContentZoneData

### Step 2: Add GeometryAbortedError Exception to geometry.py
- Add `GeometryAbortedError` exception class after imports
- Inherit from `Exception`
- Add docstring explaining its purpose for abort signaling during long operations

### Step 3: Add Helper Functions to geometry.py
- Add import for `threading` module at top of file
- Add import for `time` module at top of file
- Add import for `ContentZoneData, Polygon` from `.types`
- Add import for threshold constants from `.constants`
- Add `_empty_content_zone_data()` function returning ContentZoneData with all None values and content_zone_detected=False
- Add `_count_line_segments(block_def: BlockLayout) -> int` function
- Add `_extract_closed_lwpolylines(block_def: BlockLayout) -> list[Polygon]` function
- Add `_shoelace_area(polygon: Polygon) -> float` function using the shoelace formula
- Add `_point_in_polygon(point: tuple[float, float], polygon: Polygon) -> bool` using ray-casting algorithm
- Add `_polygon_contains_polygon(outer: Polygon, inner: Polygon) -> bool` function
- Add `_get_polygon_bbox(polygon: Polygon) -> tuple[float, float, float, float]` function

### Step 4: Add LINE Cycle Detection Function to geometry.py
- Add `_extract_line_cycles(block_def: BlockLayout, abort_event: threading.Event | None = None) -> list[Polygon]` function
- Build adjacency graph from LINE segment endpoints using coordinate rounding for tolerance
- Implement iterative DFS to find all closed cycles
- Add timeout check: break if `time.perf_counter() - start_time > CYCLE_DETECTION_TIMEOUT_SECONDS`
- Add abort checkpoint: raise `GeometryAbortedError` if `abort_event.is_set()` every 1000 iterations
- Log warning on timeout with iteration count
- Return list of detected polygons

### Step 5: Add Net Area Calculation Function to geometry.py
- Add `_calculate_net_areas(polygons: list[Polygon], abort_event: threading.Event | None = None) -> list[tuple[Polygon, float]]` function
- For each polygon, calculate gross area using `_shoelace_area()`
- Subtract areas of all contained polygons using `_polygon_contains_polygon()`
- Add abort checkpoint every 10 polygons
- Return list of (polygon, net_area) tuples
- Add docstring noting O(n^3) complexity and threshold requirement

### Step 6: Add Main Content Zone Detection Function to geometry.py
- Add `_detect_content_zone(block_def: BlockLayout, block_bbox: tuple[float, float, float, float], abort_event: threading.Event | None = None) -> ContentZoneData` function
- Extract LWPOLYLINE shapes using `_extract_closed_lwpolylines()`
- Check LINE count and conditionally extract LINE cycles
- Return `_empty_content_zone_data()` if no shapes found
- Check polygon threshold and return empty if exceeded
- Calculate net areas using `_calculate_net_areas()`
- Find polygon with largest net area
- Get content zone bbox using `_get_polygon_bbox()`
- Calculate trim values: `trim_left = cz_min_x - block_min_x`, etc.
- Return ContentZoneData with results

### Step 7: Create Content Zone Test DXF Generator Script
- Create `app/tests/assets/create_content_zone_test.py` script
- Create block "NESTED_RECTANGLES" with outer rectangle (0,0)-(100,80) and inner rectangle (10,10)-(90,70) using LWPOLYLINE
- Create block "CHAMFERED_SHAPE" with chamfered corners using LINE segments
- Create block "MIXED_SHAPES" with multiple LWPOLYLINE shapes for containment testing
- Create block "SINGLE_RECTANGLE" with one closed LWPOLYLINE
- Create block "OPEN_POLYLINE" with non-closed LWPOLYLINE (should be ignored)
- Add block references to modelspace
- Save to `app/tests/assets/content_zone_test.dxf`

### Step 8: Create Many Lines Test DXF Generator Script
- Create `app/tests/assets/create_many_lines_test.py` script
- Create block "MANY_LINES" with 500+ LINE segments (grid pattern)
- Create block "FEW_LINES" with <50 LINE segments forming simple rectangle
- Add block references to modelspace
- Save to `app/tests/assets/many_lines_test.dxf`

### Step 9: Generate Test DXF Files
- Run `uv run python app/tests/assets/create_content_zone_test.py`
- Run `uv run python app/tests/assets/create_many_lines_test.py`
- Verify files exist: `test -f app/tests/assets/content_zone_test.dxf`
- Verify files exist: `test -f app/tests/assets/many_lines_test.dxf`

### Step 10: Create Content Zone Test File Structure
- Create `app/tests/core/test_content_zone.py` with imports
- Import pytest, ezdxf, threading, time
- Import functions from `core.geometry`
- Import types from `core.types`
- Import constants from `core.constants`
- Add module docstring describing test coverage

### Step 11: Add LWPOLYLINE Detection Tests
- Add `TestLwpolylineDetection` class
- Add `test_extract_closed_lwpolyline_rectangle()` - detects closed rectangle
- Add `test_extract_closed_lwpolyline_ignores_open()` - ignores non-closed polylines
- Add `test_extract_multiple_lwpolylines()` - detects multiple shapes

### Step 12: Add LINE Cycle Detection Tests
- Add `TestLineCycleDetection` class
- Add `test_extract_line_cycle_simple_rectangle()` - detects rectangle from 4 LINE segments
- Add `test_extract_line_cycle_no_cycles()` - returns empty for open line chains
- Add `test_line_cycle_timeout()` - verify timeout protection works (mock with slow processing)

### Step 13: Add Threshold Skip Tests
- Add `TestThresholdSkips` class
- Add `test_line_threshold_skip()` - verify LINE cycle detection skipped when segment count > threshold
- Add `test_polygon_threshold_skip()` - verify net area skipped when polygon count > threshold
- Use MANY_LINES block from many_lines_test.dxf for line threshold test

### Step 14: Add Area Calculation Tests
- Add `TestAreaCalculation` class
- Add `test_shoelace_area_rectangle()` - correct area for simple rectangle
- Add `test_shoelace_area_triangle()` - correct area for triangle
- Add `test_shoelace_area_negative_winding()` - handles clockwise winding

### Step 15: Add Point-in-Polygon Tests
- Add `TestPointInPolygon` class
- Add `test_point_inside_rectangle()` - returns True for interior point
- Add `test_point_outside_rectangle()` - returns False for exterior point
- Add `test_point_on_boundary()` - handles boundary case

### Step 16: Add Containment Tests
- Add `TestContainment` class
- Add `test_polygon_contains_polygon_nested()` - detects nested polygons
- Add `test_polygon_contains_polygon_disjoint()` - returns False for disjoint polygons
- Add `test_polygon_contains_polygon_partial_overlap()` - handles partial overlap

### Step 17: Add Net Area Calculation Tests
- Add `TestNetAreaCalculation` class
- Add `test_net_area_single_polygon()` - net area equals gross area
- Add `test_net_area_nested_polygons()` - correctly subtracts contained area
- Add `test_net_area_multiple_nested()` - handles multiple levels of nesting

### Step 18: Add Trim Value Calculation Tests
- Add `TestTrimValueCalculation` class
- Add `test_trim_values_centered_content_zone()` - correct trim for centered content
- Add `test_trim_values_offset_content_zone()` - correct trim for offset content
- Add `test_trim_values_full_block_content_zone()` - zero trim when content equals block

### Step 19: Add Integration Tests
- Add `TestContentZoneDetection` class
- Add `test_detect_content_zone_nested_rectangles()` - full detection with nested shapes
- Add `test_detect_content_zone_no_shapes()` - returns empty for blocks without closed shapes
- Add `test_detect_content_zone_single_shape()` - handles single shape correctly
- Add `test_detect_content_zone_with_abort_event()` - properly handles abort

### Step 20: Add Edge Case Tests
- Add `TestEdgeCases` class
- Add `test_empty_block()` - returns empty ContentZoneData
- Add `test_degenerate_polygon()` - handles zero-area polygons
- Add `test_very_small_polygon()` - handles tiny polygons correctly
- Add `test_concurrent_polygons()` - handles overlapping but non-nested polygons

### Step 21: Run Validation Commands
- Run `uv run pytest app/tests/core/test_content_zone.py -v` to verify new tests pass
- Run `uv run pytest app/tests/` to verify all tests pass (should be 392+ original + new)
- Run `uv run mypy app/` for type checking
- Run `uv run ruff check app/` for linting
- Run `uv run ruff format app/` for formatting
- Run `uv run ruff check app/ --fix` for auto-fixes

## Testing Strategy
### Unit Tests
- `_empty_content_zone_data()` - returns correct default values
- `_count_line_segments()` - correctly counts LINE entities
- `_extract_closed_lwpolylines()` - extracts only closed polylines
- `_shoelace_area()` - correct area calculation for various polygon shapes
- `_point_in_polygon()` - correct inside/outside/boundary detection
- `_polygon_contains_polygon()` - correct containment detection
- `_get_polygon_bbox()` - correct bounding box extraction
- `_extract_line_cycles()` - correct cycle detection with timeout/abort
- `_calculate_net_areas()` - correct net area with containment subtraction

### Integration Tests
- `_detect_content_zone()` with NESTED_RECTANGLES block - full pipeline test
- `_detect_content_zone()` with threshold skip scenarios
- `_detect_content_zone()` with abort event handling

### Edge Cases
- Empty block (no entities)
- Block with only open polylines
- Block with only non-geometric entities (TEXT, etc.)
- Block with exactly threshold number of polygons/segments
- Block with polygons that share edges but don't contain each other
- Block with concave polygons
- Block with self-intersecting polylines (degenerate)
- Zero-area polygons (collinear points)
- Very large polygons with many vertices
- Timeout during cycle detection
- Abort event during processing

### Playwright MCP Tests
Not applicable - this feature is computational geometry with no GUI components. Unit and integration tests provide complete coverage.

## Acceptance Criteria
1. `Polygon` type alias exists in `app/core/types.py`
2. `ContentZoneData` TypedDict exists with all required fields
3. `GeometryAbortedError` exception class exists in `app/core/geometry.py`
4. `_extract_closed_lwpolylines()` correctly extracts closed LWPOLYLINE shapes
5. `_extract_line_cycles()` correctly detects cycles from LINE segments
6. LINE cycle detection is skipped when segment count > LINE_SEGMENT_THRESHOLD (200)
7. Cycle detection times out after CYCLE_DETECTION_TIMEOUT_SECONDS (5.0)
8. `_shoelace_area()` correctly calculates polygon areas
9. `_point_in_polygon()` correctly determines containment
10. `_calculate_net_areas()` correctly computes net area (own - contained)
11. Net area calculation is skipped when polygon count > POLYGON_COUNT_THRESHOLD (30)
12. `_detect_content_zone()` selects shape with largest net area
13. Trim values are correctly derived from content zone bbox relative to block bbox
14. All abort checkpoints properly check and raise `GeometryAbortedError`
15. Test DXF files created: `content_zone_test.dxf`, `many_lines_test.dxf`
16. All existing tests pass (392+)
17. All new content zone tests pass
18. mypy type checking passes
19. ruff linting passes

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- Generate test DXF files:
    - `uv run python app/tests/assets/create_content_zone_test.py`
    - `uv run python app/tests/assets/create_many_lines_test.py`
- Run tests to validate the feature works with zero regressions:
    - `uv run pytest app/tests/core/test_content_zone.py -v`
    - `uv run pytest app/tests/`
    - `uv run mypy app/`
    - `uv run ruff check app/`
    - `uv run ruff format app/`
    - `uv run ruff check app/ --fix`

## Notes
- The threshold values (POLYGON_COUNT_THRESHOLD=30, LINE_SEGMENT_THRESHOLD=200, CYCLE_DETECTION_TIMEOUT_SECONDS=5.0) are already defined in `app/core/constants.py` from US-1.
- The logging infrastructure (FlushingFileHandler, create_debug_file_handler) is already available from US-2.
- The coordinate tolerance for LINE segment endpoint matching should use the same epsilon (0.01) as existing geometry functions.
- The shoelace formula handles both clockwise and counter-clockwise winding by taking absolute value.
- The ray-casting algorithm for point-in-polygon uses a horizontal ray and counts crossings.
- For LINE cycle detection, coordinates are rounded to 2 decimal places to create adjacency graph keys, matching the existing segment calculation precision.
- The DFS implementation should be iterative (not recursive) to avoid stack overflow on large graphs.
- Net area calculation assumes simple polygons (no self-intersection). Degenerate cases return zero area.
- This is the core algorithm unit - subsequent user stories will integrate it with the extractor and Excel writer.
