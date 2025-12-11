# Chore: Unit 2 - Nested Polygon Test Assets Creation

## Chore Description

Create test DXF files and generator scripts for nested polygon scenarios to support Unit 3 tests of the net area filter implementation. This is Phase 2 of the Net Area Filter Implementation Plan (`ai_output/025-net-area-filter-implementation-plan.md`).

The test assets will provide controlled test cases for validating that the area filter correctly uses NET area (gross area minus contained polygon areas) instead of GROSS area. These test cases are essential for verifying the core logic change implemented in Unit 1.

**Files to create:**
- `app/tests/assets/create_nested_polygon_filter_test.py` - Generator script
- `app/tests/assets/nested_polygon_filter_test.dxf` - Generated test asset

**Blocks to create in the DXF file:**

| Block Name | Description | Outer Dimensions | Inner Dimensions | Expected Net Areas |
|------------|-------------|------------------|------------------|-------------------|
| `PICTURE_FRAME` | Outer rectangle containing centered inner rectangle | 100x100 (gross=10000) | 80x80 (gross=6400) | Outer net=3600, Inner net=6400 |
| `BOX_IN_BOX_IN_BOX` | 3 nested boxes with decreasing sizes | 100x100 | 80x80, then 50x50 | Outer=3600, Middle=3900, Inner=2500 |
| `MULTIPLE_SIBLINGS` | Outer containing 3 non-overlapping inner rectangles | 100x100 | 3x (20x20=400 each) | Outer net=8800, Each sibling=400 |
| `SINGLE_LARGE` | Single rectangle for comparison (no nesting) | 80x80 | None | Net=6400 (same as gross) |

**Key design points:**
- Each block should have closed LWPOLYLINE boundaries
- Use consistent layer naming (`BOUNDARY`)
- Block positions should be well-separated (150+ units apart) to avoid overlap
- Polygons are centered within outer boundaries for predictable net area calculations
- All coordinates use integer values for precise testing

## Relevant Files

Use these files to resolve the chore:

- **`app/tests/assets/create_content_zone_test.py`** - Reference generator script showing pattern for creating blocks with nested LWPOLYLINE shapes. Demonstrates:
  - Script structure with docstring explaining block contents
  - Using `ezdxf.new("R2010")` for DXF version
  - Creating blocks with `doc.blocks.new(name="...")`
  - Adding closed LWPOLYLINE with `block.add_lwpolyline([...], close=True)`
  - Adding block references to modelspace with positions
  - Saving to `app/tests/assets/` directory

- **`app/tests/assets/create_equal_area_test.py`** - Reference generator script showing function-based pattern with `if __name__ == "__main__"` guard. Demonstrates:
  - Wrapping creation in a function `create_*()` for reusability
  - Using LINE entities to establish block bounding box
  - Creating multiple shapes within a single block

- **`ai_output/025-net-area-filter-implementation-plan.md`** - Implementation plan containing the expected test block specifications and net area calculations

- **`specs/043-unit-1-net-area-filter-core-logic.md`** - Unit 1 spec with context on the filtering logic being tested

### New Files

- **`app/tests/assets/create_nested_polygon_filter_test.py`** - New generator script to create the test DXF file with nested polygon blocks
- **`app/tests/assets/nested_polygon_filter_test.dxf`** - Generated DXF test file (created by running the generator script)

## Step by Step Tasks

### Step 1: Create the Generator Script File

Create `app/tests/assets/create_nested_polygon_filter_test.py` with:

1. Module docstring explaining the purpose and listing all blocks with their expected net areas
2. Import `ezdxf`
3. Define a `create_nested_polygon_filter_test()` function

### Step 2: Implement PICTURE_FRAME Block

Create a block demonstrating the "picture frame" scenario where a large outer polygon has a small net area:

- Outer rectangle: corners at (0, 0) to (100, 100) = 10,000 sq units gross
- Inner rectangle: corners at (10, 10) to (90, 90) = 6,400 sq units gross
- Expected net areas: Outer = 10,000 - 6,400 = 3,600; Inner = 6,400
- With min_area_filter=5000: Outer should fail (3,600 < 5,000), Inner should pass (6,400 > 5,000)

Both shapes should use closed LWPOLYLINE on layer `BOUNDARY`.

### Step 3: Implement BOX_IN_BOX_IN_BOX Block

Create a block with 3 levels of nesting to test multi-level containment:

- Outermost: (0, 0) to (100, 100) = 10,000 sq units gross
- Middle: (10, 10) to (90, 90) = 6,400 sq units gross
- Innermost: (25, 25) to (75, 75) = 2,500 sq units gross
- Expected net areas:
  - Outermost: 10,000 - 6,400 = 3,600 (contains middle)
  - Middle: 6,400 - 2,500 = 3,900 (contains innermost)
  - Innermost: 2,500 (contains nothing)

All shapes should use closed LWPOLYLINE on layer `BOUNDARY`.

### Step 4: Implement MULTIPLE_SIBLINGS Block

Create a block with one outer and multiple non-overlapping inner rectangles:

- Outer: (0, 0) to (100, 100) = 10,000 sq units gross
- Inner 1: (10, 10) to (30, 30) = 400 sq units (bottom-left)
- Inner 2: (40, 40) to (60, 60) = 400 sq units (center)
- Inner 3: (70, 70) to (90, 90) = 400 sq units (top-right)
- Expected net areas:
  - Outer: 10,000 - 400 - 400 - 400 = 8,800
  - Each inner: 400 (no containment between siblings)

All shapes should use closed LWPOLYLINE on layer `BOUNDARY`.

### Step 5: Implement SINGLE_LARGE Block

Create a single rectangle block for comparison (no nesting):

- Single rectangle: (0, 0) to (80, 80) = 6,400 sq units
- Expected net area: 6,400 (gross = net when no containment)

This block provides a baseline to compare against nested scenarios.

### Step 6: Add Block References to Modelspace

Add block references to modelspace with well-separated positions:

- `PICTURE_FRAME` at (0, 0)
- `BOX_IN_BOX_IN_BOX` at (150, 0)
- `MULTIPLE_SIBLINGS` at (300, 0)
- `SINGLE_LARGE` at (450, 0)

The 150-unit spacing ensures no overlap between block bounding boxes.

### Step 7: Add Main Guard and Save Logic

Add the `if __name__ == "__main__"` guard and save logic:

```python
if __name__ == "__main__":
    create_nested_polygon_filter_test()
```

Save the DXF file to `app/tests/assets/nested_polygon_filter_test.dxf`.

### Step 8: Run the Generator Script

Execute the generator script to create the DXF file:

```bash
uv run python app/tests/assets/create_nested_polygon_filter_test.py
```

Verify the script outputs a success message and the DXF file is created.

### Step 9: Verify DXF File Structure

Use ezdxf to verify the generated DXF file contains the expected blocks:

```bash
uv run python -c "
import ezdxf
doc = ezdxf.readfile('app/tests/assets/nested_polygon_filter_test.dxf')
blocks = [b.name for b in doc.blocks if not b.name.startswith('*')]
print('Blocks:', sorted(blocks))
print('Block count:', len(blocks))
"
```

Expected output should list: `PICTURE_FRAME`, `BOX_IN_BOX_IN_BOX`, `MULTIPLE_SIBLINGS`, `SINGLE_LARGE`

### Step 10: Verify Block Contents

Verify each block contains the expected number of LWPOLYLINE entities:

```bash
uv run python -c "
import ezdxf
doc = ezdxf.readfile('app/tests/assets/nested_polygon_filter_test.dxf')
for block_name in ['PICTURE_FRAME', 'BOX_IN_BOX_IN_BOX', 'MULTIPLE_SIBLINGS', 'SINGLE_LARGE']:
    block = doc.blocks[block_name]
    polylines = [e for e in block if e.dxftype() == 'LWPOLYLINE']
    print(f'{block_name}: {len(polylines)} LWPOLYLINE entities')
"
```

Expected output:
- PICTURE_FRAME: 2 LWPOLYLINE entities
- BOX_IN_BOX_IN_BOX: 3 LWPOLYLINE entities
- MULTIPLE_SIBLINGS: 4 LWPOLYLINE entities
- SINGLE_LARGE: 1 LWPOLYLINE entity

### Step 11: Run Linting on Generator Script

Verify the generator script passes linting:

```bash
uv run ruff check app/tests/assets/create_nested_polygon_filter_test.py
uv run ruff format app/tests/assets/create_nested_polygon_filter_test.py --check
```

### Step 12: Run Existing Tests

Run the existing test suite to ensure no regressions from adding new files:

```bash
uv run pytest app/tests/ -v
```

All existing tests should continue to pass.

## Validation Commands

Execute every command to validate the chore is complete with zero regressions.

- `uv run python app/tests/assets/create_nested_polygon_filter_test.py` - Run the generator script to create the DXF file
- `test -f app/tests/assets/nested_polygon_filter_test.dxf && echo "DXF file exists"` - Verify DXF file was created
- `uv run python -c "import ezdxf; doc = ezdxf.readfile('app/tests/assets/nested_polygon_filter_test.dxf'); blocks = [b.name for b in doc.blocks if not b.name.startswith('*')]; print('Blocks:', sorted(blocks)); assert len(blocks) == 4, f'Expected 4 blocks, got {len(blocks)}'"` - Verify DXF contains exactly 4 blocks
- `uv run ruff check app/tests/assets/create_nested_polygon_filter_test.py` - Lint the generator script
- `uv run ruff format app/tests/assets/create_nested_polygon_filter_test.py --check` - Verify generator script formatting
- `uv run pytest app/tests/ -v` - Run all tests to ensure zero regressions

## Notes

### Net Area Calculation Reference

The net area for a polygon is calculated as: `net_area = gross_area - sum(contained_polygon_areas)`

The `_calculate_net_areas()` function in `geometry.py` handles this calculation. The test assets created here will be used in Unit 3 to verify that `min_area_filter` correctly uses these net areas.

### Test Scenario: Picture Frame with Filter=5000

The primary use case being tested:
1. PICTURE_FRAME block has outer (net=3600) and inner (net=6400)
2. With `min_area_filter=5000`:
   - **Before Unit 1 (gross)**: Both pass (10000 > 5000, 6400 > 5000) - outer wins as largest gross
   - **After Unit 1 (net)**: Outer fails (3600 < 5000), inner passes (6400 > 5000) - inner correctly wins

### Layer Convention

All LWPOLYLINE entities use the default layer (layer `0`). The existing generator scripts in the codebase do not explicitly set layers for LWPOLYLINE entities, and the geometry extraction code does not filter by layer when detecting content zones.

### Coordinate System

All coordinates use positive integer values starting from (0, 0) for each block's local coordinate system. The block references in modelspace are positioned at different X coordinates to ensure visual separation when viewing the DXF file.

### Unit Relationships

- **Unit 1** (completed): Core logic change in `_detect_content_zone()` to filter by net area
- **Unit 2** (this spec): Test asset creation for nested polygon scenarios
- **Unit 3** (upcoming): Unit tests using these assets to verify net area filtering
- **Unit 4** (upcoming): Integration tests via `extract_blocks()`
