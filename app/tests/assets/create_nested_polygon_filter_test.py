"""
Generate test DXF file with nested polygon scenarios for net area filter testing.

This file contains blocks with various nesting configurations:

- PICTURE_FRAME: Outer 100x100 (gross=10000) containing inner 80x80 (gross=6400)
  - Outer net area: 10000 - 6400 = 3600
  - Inner net area: 6400 (no children)

- BOX_IN_BOX_IN_BOX: 3 nested rectangles
  - Outermost 100x100 (gross=10000), net = 10000 - 6400 = 3600
  - Middle 80x80 (gross=6400), net = 6400 - 2500 = 3900
  - Innermost 50x50 (gross=2500), net = 2500

- MULTIPLE_SIBLINGS: Outer containing 3 non-overlapping inner rectangles
  - Outer 100x100 (gross=10000), net = 10000 - 400 - 400 - 400 = 8800
  - Each inner 20x20 (gross=400), net = 400

- SINGLE_LARGE: Single rectangle 80x80 for comparison (no nesting)
  - Net area = 6400 (same as gross)

Test scenario: With min_area_filter=5000:
- PICTURE_FRAME outer (net=3600) should FAIL, inner (net=6400) should PASS
- BOX_IN_BOX_IN_BOX: outer (3600) FAIL, middle (3900) FAIL, inner (2500) FAIL
- MULTIPLE_SIBLINGS: outer (8800) PASS, siblings (400 each) FAIL
- SINGLE_LARGE: (6400) PASS
"""

import ezdxf


def create_nested_polygon_filter_test() -> None:
    """Create DXF with nested polygon blocks for net area filter testing."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Block 1: PICTURE_FRAME - Outer with centered inner rectangle
    # Demonstrates "picture frame" scenario where outer has small net area
    block_frame = doc.blocks.new("PICTURE_FRAME")
    # Outer rectangle: (0, 0) to (100, 100) = 10,000 sq units gross
    block_frame.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
    )
    # Inner rectangle: (10, 10) to (90, 90) = 6,400 sq units gross
    # Centered within outer, leaving 10-unit border on all sides
    block_frame.add_lwpolyline(
        [(10, 10), (90, 10), (90, 90), (10, 90)],
        close=True,
    )

    # Block 2: BOX_IN_BOX_IN_BOX - 3 levels of nesting
    # Tests multi-level containment handling
    block_nested = doc.blocks.new("BOX_IN_BOX_IN_BOX")
    # Outermost: (0, 0) to (100, 100) = 10,000 sq units gross
    block_nested.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
    )
    # Middle: (10, 10) to (90, 90) = 6,400 sq units gross
    block_nested.add_lwpolyline(
        [(10, 10), (90, 10), (90, 90), (10, 90)],
        close=True,
    )
    # Innermost: (25, 25) to (75, 75) = 2,500 sq units gross
    block_nested.add_lwpolyline(
        [(25, 25), (75, 25), (75, 75), (25, 75)],
        close=True,
    )

    # Block 3: MULTIPLE_SIBLINGS - Outer with 3 non-overlapping inner rectangles
    # Tests sibling containment (no containment between inner rectangles)
    block_siblings = doc.blocks.new("MULTIPLE_SIBLINGS")
    # Outer: (0, 0) to (100, 100) = 10,000 sq units gross
    block_siblings.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
    )
    # Inner 1: bottom-left corner (10, 10) to (30, 30) = 400 sq units
    block_siblings.add_lwpolyline(
        [(10, 10), (30, 10), (30, 30), (10, 30)],
        close=True,
    )
    # Inner 2: center (40, 40) to (60, 60) = 400 sq units
    block_siblings.add_lwpolyline(
        [(40, 40), (60, 40), (60, 60), (40, 60)],
        close=True,
    )
    # Inner 3: top-right corner (70, 70) to (90, 90) = 400 sq units
    block_siblings.add_lwpolyline(
        [(70, 70), (90, 70), (90, 90), (70, 90)],
        close=True,
    )

    # Block 4: SINGLE_LARGE - Single rectangle for comparison (no nesting)
    # Net area equals gross area when there are no contained polygons
    block_single = doc.blocks.new("SINGLE_LARGE")
    # Single rectangle: (0, 0) to (80, 80) = 6,400 sq units
    block_single.add_lwpolyline(
        [(0, 0), (80, 0), (80, 80), (0, 80)],
        close=True,
    )

    # Add block references to modelspace with 150-unit spacing
    msp.add_blockref("PICTURE_FRAME", (0, 0))
    msp.add_blockref("BOX_IN_BOX_IN_BOX", (150, 0))
    msp.add_blockref("MULTIPLE_SIBLINGS", (300, 0))
    msp.add_blockref("SINGLE_LARGE", (450, 0))

    # Save the file
    doc.saveas("app/tests/assets/nested_polygon_filter_test.dxf")
    print("Created app/tests/assets/nested_polygon_filter_test.dxf")


if __name__ == "__main__":
    create_nested_polygon_filter_test()
