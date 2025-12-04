"""
Create test DXF file with various content zone detection scenarios.

This script generates a DXF file containing blocks with different polygon configurations
for testing the content zone detection feature:
- Simple nested rectangles (LWPOLYLINE)
- Chamfered rectangles (8-vertex polygons)
- LINE-based closed shapes
- Mixed LWPOLYLINE and LINE shapes
- Single shape (no nesting)
- No closed shapes
- Equal area shapes
"""

import ezdxf


def create_content_zone_test_dxf(output_path: str) -> None:
    """Create a test DXF file with various content zone scenarios."""
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()

    # Block 1: Simple nested rectangles using LWPOLYLINE
    # Outer: 100x50, Inner: 80x30 (centered, so 10 offset on each side)
    block1 = doc.blocks.new(name="NESTED_RECTANGLES")
    # Outer rectangle
    block1.add_lwpolyline(
        [(0, 0), (100, 0), (100, 50), (0, 50)],
        close=True,
    )
    # Inner rectangle (content zone - net area = 80*30 = 2400)
    block1.add_lwpolyline(
        [(10, 10), (90, 10), (90, 40), (10, 40)],
        close=True,
    )

    # Block 2: Chamfered outer rectangle (8-vertex polygon) with inner rectangle
    # Tests non-rectangular content zone bounding box
    block2 = doc.blocks.new(name="CHAMFERED_OUTER")
    # Outer chamfered rectangle (corners cut off)
    block2.add_lwpolyline(
        [
            (5, 0),
            (95, 0),
            (100, 5),
            (100, 45),
            (95, 50),
            (5, 50),
            (0, 45),
            (0, 5),
        ],
        close=True,
    )
    # Inner rectangle
    block2.add_lwpolyline(
        [(15, 10), (85, 10), (85, 40), (15, 40)],
        close=True,
    )

    # Block 3: LINE-based closed rectangle (tests LINE cycle detection)
    block3 = doc.blocks.new(name="LINE_RECTANGLE")
    # Create a rectangle using LINE entities
    block3.add_line((0, 0), (80, 0))
    block3.add_line((80, 0), (80, 40))
    block3.add_line((80, 40), (0, 40))
    block3.add_line((0, 40), (0, 0))
    # Inner rectangle using lines (content zone)
    block3.add_line((10, 10), (70, 10))
    block3.add_line((70, 10), (70, 30))
    block3.add_line((70, 30), (10, 30))
    block3.add_line((10, 30), (10, 10))

    # Block 4: Mixed LWPOLYLINE and LINE shapes
    block4 = doc.blocks.new(name="MIXED_SHAPES")
    # Outer rectangle using LWPOLYLINE
    block4.add_lwpolyline(
        [(0, 0), (120, 0), (120, 60), (0, 60)],
        close=True,
    )
    # Inner rectangle using LINEs (content zone)
    block4.add_line((20, 15), (100, 15))
    block4.add_line((100, 15), (100, 45))
    block4.add_line((100, 45), (20, 45))
    block4.add_line((20, 45), (20, 15))

    # Block 5: Single shape (no nesting - the shape itself is the content zone)
    block5 = doc.blocks.new(name="SINGLE_SHAPE")
    block5.add_lwpolyline(
        [(0, 0), (50, 0), (50, 30), (0, 30)],
        close=True,
    )

    # Block 6: No closed shapes (only open polylines and standalone lines)
    block6 = doc.blocks.new(name="NO_CLOSED_SHAPES")
    # Open polyline (not closed)
    block6.add_lwpolyline(
        [(0, 0), (50, 0), (50, 30)],
        close=False,
    )
    # Disconnected lines
    block6.add_line((0, 0), (10, 10))
    block6.add_line((20, 20), (30, 30))

    # Block 7: Two equal area shapes (tests deterministic ordering)
    # Both have area = 1000, first detected (LWPOLYLINE) should be content zone
    block7 = doc.blocks.new(name="EQUAL_AREAS")
    block7.add_lwpolyline(
        [(0, 0), (50, 0), (50, 20), (0, 20)],
        close=True,
    )
    block7.add_lwpolyline(
        [(60, 0), (110, 0), (110, 20), (60, 20)],
        close=True,
    )

    # Block 8: Triple nesting (outer > middle > inner)
    # Tests that net area calculation properly handles multiple containment levels
    block8 = doc.blocks.new(name="TRIPLE_NESTING")
    # Outer: 100x100 = 10000
    block8.add_lwpolyline(
        [(0, 0), (100, 0), (100, 100), (0, 100)],
        close=True,
    )
    # Middle: 80x80 = 6400 (centered)
    block8.add_lwpolyline(
        [(10, 10), (90, 10), (90, 90), (10, 90)],
        close=True,
    )
    # Inner: 40x40 = 1600 (centered)
    block8.add_lwpolyline(
        [(30, 30), (70, 30), (70, 70), (30, 70)],
        close=True,
    )

    # Insert blocks into modelspace for the extraction pipeline
    msp.add_blockref("NESTED_RECTANGLES", (0, 0))
    msp.add_blockref("CHAMFERED_OUTER", (150, 0))
    msp.add_blockref("LINE_RECTANGLE", (300, 0))
    msp.add_blockref("MIXED_SHAPES", (0, 100))
    msp.add_blockref("SINGLE_SHAPE", (150, 100))
    msp.add_blockref("NO_CLOSED_SHAPES", (300, 100))
    msp.add_blockref("EQUAL_AREAS", (0, 200))
    msp.add_blockref("TRIPLE_NESTING", (150, 200))

    doc.saveas(output_path)
    print(f"Created test DXF file: {output_path}")


if __name__ == "__main__":
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, "content_zone_test.dxf")
    create_content_zone_test_dxf(output_file)
