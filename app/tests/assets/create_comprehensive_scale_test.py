"""
Creates a DXF file with a block and multiple instances at different scales.

This test file includes:
- A simple rectangular block (1000x2000 units)
- Normal scale instances
- Negative scale instances (flipped horizontally, vertically, both)
- 10x scale instances (X-axis, Y-axis, both axes)
"""

import ezdxf
from pathlib import Path


def create_comprehensive_scale_test() -> None:
    """Create a DXF with block instances at various scales including negatives and 10x."""
    # Create new DXF document
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create block definition with a 1000x2000 rectangle
    block = doc.blocks.new(name="TEST_RECT_1000x2000")
    # Rectangle from (0,0) to (1000,2000)
    block.add_lwpolyline(
        [(0, 0), (1000, 0), (1000, 2000), (0, 2000), (0, 0)],
        close=True
    )

    # Position offset for layout (spacing between instances)
    # Need enough space for 10x scaled blocks (10000 x 20000) plus margin
    # Negative scales flip the block, so we need extra space in both directions
    x_spacing = 25000  # Accommodates 10x X-scale in both directions + margin
    y_spacing = 45000  # Accommodates 10x Y-scale in both directions + margin
    col = 0
    row = 0

    # Test cases: (description, x_scale, y_scale, z_scale)
    test_cases = [
        ("Normal scale", 1.0, 1.0, 1.0),
        ("Negative X (horizontal flip)", -1.0, 1.0, 1.0),
        ("Negative Y (vertical flip)", 1.0, -1.0, 1.0),
        ("Negative X and Y (both flip)", -1.0, -1.0, 1.0),
        ("10x scale X-axis", 10.0, 1.0, 1.0),
        ("10x scale Y-axis", 1.0, 10.0, 1.0),
        ("10x scale both axes", 10.0, 10.0, 1.0),
        ("Negative X with 10x Y", -1.0, 10.0, 1.0),
        ("10x X with negative Y", 10.0, -1.0, 1.0),
    ]

    # Insert block instances with different scales
    for description, x_scale, y_scale, z_scale in test_cases:
        # Add offset to center the insertion point in the cell
        # This prevents negative scales from extending into adjacent cells
        insert_x = col * x_spacing + 12000
        insert_y = row * y_spacing + 22000

        # Add block reference
        msp.add_blockref(
            "TEST_RECT_1000x2000",
            (insert_x, insert_y),
            dxfattribs={
                "xscale": x_scale,
                "yscale": y_scale,
                "zscale": z_scale,
            }
        )

        # Add text label below the block
        msp.add_text(
            description,
            dxfattribs={
                "insert": (insert_x, insert_y - 500),
                "height": 100,
            }
        )

        # Layout in grid (3 columns)
        col += 1
        if col >= 3:
            col = 0
            row += 1

    # Save the DXF file
    output_path = Path(__file__).parent / "comprehensive_scale_test.dxf"
    doc.saveas(output_path)
    print(f"Created: {output_path}")
    print(f"Block instances: {len(test_cases)}")


if __name__ == "__main__":
    create_comprehensive_scale_test()
