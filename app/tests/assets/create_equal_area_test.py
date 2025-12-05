"""
Create test DXF file for union bounding box testing with equal area shapes.

This script creates a DXF file with blocks containing:
- FOUR_CORNERS: 4 equal 10x10 rectangles at corners of a 100x100 area
- TWO_EQUAL_HORIZONTAL: 2 equal 20x10 rectangles side by side
- SINGLE_SHAPE: 1 rectangle for regression testing

Usage:
    uv run python app/tests/assets/create_equal_area_test.py
"""

from pathlib import Path

import ezdxf


def create_equal_area_test_dxf() -> None:
    """Create test DXF file with equal area shapes for union bounding box testing."""
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Block 1: FOUR_CORNERS - 4 equal 10x10 rectangles at corners of 100x100 area
    # This tests the union bounding box when 4 shapes tie for max net area
    four_corners = doc.blocks.new(name="FOUR_CORNERS")
    # Bottom-left: (0, 0) to (10, 10)
    four_corners.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)
    # Bottom-right: (90, 0) to (100, 10)
    four_corners.add_lwpolyline([(90, 0), (100, 0), (100, 10), (90, 10)], close=True)
    # Top-left: (0, 90) to (10, 100)
    four_corners.add_lwpolyline([(0, 90), (10, 90), (10, 100), (0, 100)], close=True)
    # Top-right: (90, 90) to (100, 100)
    four_corners.add_lwpolyline(
        [(90, 90), (100, 90), (100, 100), (90, 100)], close=True
    )

    # Block 2: TWO_EQUAL_HORIZONTAL - 2 equal 20x10 rectangles side by side
    # This tests union bounding box with 2 tied shapes
    two_equal = doc.blocks.new(name="TWO_EQUAL_HORIZONTAL")
    # Left rectangle: (0, 0) to (20, 10)
    two_equal.add_lwpolyline([(0, 0), (20, 0), (20, 10), (0, 10)], close=True)
    # Right rectangle: (80, 0) to (100, 10)
    two_equal.add_lwpolyline([(80, 0), (100, 0), (100, 10), (80, 10)], close=True)

    # Block 3: SINGLE_SHAPE - one 50x30 rectangle (regression test)
    # This ensures single-shape behavior is preserved
    single_shape = doc.blocks.new(name="SINGLE_SHAPE")
    single_shape.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)

    # Add block references in modelspace for completeness
    msp.add_blockref("FOUR_CORNERS", (0, 0))
    msp.add_blockref("TWO_EQUAL_HORIZONTAL", (0, 150))
    msp.add_blockref("SINGLE_SHAPE", (0, 300))

    # Save to assets directory
    output_path = Path(__file__).parent / "equal_area_test.dxf"
    doc.saveas(output_path)
    print(f"Created: {output_path}")


if __name__ == "__main__":
    create_equal_area_test_dxf()
