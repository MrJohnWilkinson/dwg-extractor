"""Generate test DXF file with equal-area shapes for union bounding box testing."""

import ezdxf


def create_equal_area_test() -> None:
    """Create DXF with blocks having multiple equal-area shapes."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Block 1: Four equal rectangles in corners (for tied area testing)
    # Block bbox is 100x100, each corner has 10x10 rectangle
    block1 = doc.blocks.new("EQUAL_CORNERS")
    # Bottom-left corner
    block1.add_lwpolyline(
        [(0, 0), (10, 0), (10, 10), (0, 10)],
        close=True,
    )
    # Bottom-right corner
    block1.add_lwpolyline(
        [(90, 0), (100, 0), (100, 10), (90, 10)],
        close=True,
    )
    # Top-left corner
    block1.add_lwpolyline(
        [(0, 90), (10, 90), (10, 100), (0, 100)],
        close=True,
    )
    # Top-right corner
    block1.add_lwpolyline(
        [(90, 90), (100, 90), (100, 100), (90, 100)],
        close=True,
    )
    # Add outer frame LINE entities to establish block bbox
    block1.add_line((0, 0), (100, 0))
    block1.add_line((100, 0), (100, 100))
    block1.add_line((100, 100), (0, 100))
    block1.add_line((0, 100), (0, 0))

    # Block 2: Single large rectangle for comparison
    block2 = doc.blocks.new("SINGLE_LARGE")
    block2.add_lwpolyline(
        [(10, 10), (90, 10), (90, 90), (10, 90)],
        close=True,
    )
    # Outer frame
    block2.add_line((0, 0), (100, 0))
    block2.add_line((100, 0), (100, 100))
    block2.add_line((100, 100), (0, 100))
    block2.add_line((0, 100), (0, 0))

    # Add block references to modelspace
    msp.add_blockref("EQUAL_CORNERS", (0, 0))
    msp.add_blockref("SINGLE_LARGE", (150, 0))

    # Save the file
    doc.saveas("app/tests/assets/equal_area_test.dxf")
    print("Created app/tests/assets/equal_area_test.dxf")


if __name__ == "__main__":
    create_equal_area_test()
