"""
Creates a compact DXF file with a block and multiple instances at different scales.

This compact version features:
- A simple rectangular block (1000x2000 units)
- 2-column grid layout for larger, more visible blocks
- Grid lines for clear alignment reference
- Large text labels (600 units) for easy printout readability
- Border rectangles around each grid cell
- Axis reference lines at X=0 and Y=0
"""

import ezdxf
from pathlib import Path


def create_comprehensive_scale_test_compact() -> None:
    """Create a compact DXF with block instances at various scales with visual grid."""
    # Create new DXF document
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Create "walls" layer for all grid lines
    doc.layers.add("walls", color=8)  # Gray color

    # Create block definition with a 1000x2000 rectangle
    # Origin at top-left (0,0), extends right to (1000,0) and down to (1000,-2000)
    block = doc.blocks.new(name="TEST_RECT_1000x2000")
    # Rectangle from (0,0) top-left to (1000,-2000) bottom-right
    block.add_lwpolyline(
        [(0, 0), (1000, 0), (1000, -2000), (0, -2000), (0, 0)],
        close=True
    )

    # Grid layout configuration
    # 2-column layout for larger, more visible blocks
    x_spacing = 8000  # Reduced spacing for 3x scaled blocks
    y_spacing = 12000  # Reduced spacing for 3x scaled blocks
    num_columns = 2

    # Buffer margin between foundation walls and grid
    margin = 2000

    # Block base dimensions (from block definition)
    block_width = 1000
    block_height = 2000

    # Test cases: (description, x_scale, y_scale, z_scale)
    test_cases = [
        ("Normal scale", 1.0, 1.0, 1.0),
        ("Negative X (horizontal flip)", -1.0, 1.0, 1.0),
        ("Negative Y (vertical flip)", 1.0, -1.0, 1.0),
        ("Negative X and Y (both flip)", -1.0, -1.0, 1.0),
        ("3x scale X-axis", 3.0, 1.0, 1.0),
        ("3x scale Y-axis", 1.0, 3.0, 1.0),
        ("3x scale both axes", 3.0, 3.0, 1.0),
        ("Negative X with 3x Y", -1.0, 3.0, 1.0),
        ("3x X with negative Y", 3.0, -1.0, 1.0),
    ]

    # Calculate grid dimensions for drawing borders
    num_rows = (len(test_cases) + num_columns - 1) // num_columns
    grid_width = num_columns * x_spacing
    grid_height = num_rows * y_spacing

    # Calculate foundation dimensions to encompass everything with margins
    # margin + grid + spacing + legend + margin
    legend_spacing = 1500  # Space between grid and legend
    estimated_legend_width = 24000  # Estimated width for text at 700 height
    foundation_width = margin + grid_width + legend_spacing + estimated_legend_width + margin
    foundation_height = margin + grid_height + margin

    # Draw foundation rectangle starting at (0,0) on "walls" layer
    msp.add_lwpolyline(
        [
            (0, 0),
            (foundation_width, 0),
            (foundation_width, foundation_height),
            (0, foundation_height),
            (0, 0)
        ],
        close=True,
        dxfattribs={"layer": "walls"}
    )

    # Draw grid cell borders on "walls" layer (with margin offset)
    for row in range(num_rows):
        for col in range(num_columns):
            cell_x = margin + col * x_spacing
            cell_y = margin + row * y_spacing
            # Draw cell border rectangle
            msp.add_lwpolyline(
                [
                    (cell_x, cell_y),
                    (cell_x + x_spacing, cell_y),
                    (cell_x + x_spacing, cell_y + y_spacing),
                    (cell_x, cell_y + y_spacing),
                    (cell_x, cell_y)
                ],
                close=True,
                dxfattribs={"layer": "walls"}
            )

    # Draw horizontal grid lines on "walls" layer - using lwpolyline (with margin offset)
    for row in range(num_rows + 1):
        y = margin + row * y_spacing
        msp.add_lwpolyline(
            [(margin, y), (margin + grid_width, y)],
            dxfattribs={"layer": "walls"}
        )

    # Draw vertical grid lines on "walls" layer - using lwpolyline (with margin offset)
    for col in range(num_columns + 1):
        x = margin + col * x_spacing
        msp.add_lwpolyline(
            [(x, margin), (x, margin + grid_height)],
            dxfattribs={"layer": "walls"}
        )

    # Insert block instances with different scales and collect descriptions by row
    col = 0
    row = 0
    row_descriptions: dict[int, dict[str, str]] = {}  # Store descriptions by row: {row: {"left": desc, "right": desc}}

    for description, x_scale, y_scale, z_scale in test_cases:
        # Calculate cell's top-left corner (with margin offset)
        cell_x = margin + col * x_spacing
        cell_y = margin + (row + 1) * y_spacing

        # Adjust insertion point so final geometry ends up in top-left corner
        # For negative scales, block flips and extends in opposite direction
        insert_x = cell_x + (block_width * abs(x_scale) if x_scale < 0 else 0)
        insert_y = cell_y - (block_height * abs(y_scale) if y_scale < 0 else 0)

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

        # Store description for legend
        if row not in row_descriptions:
            row_descriptions[row] = {}
        row_descriptions[row]["left" if col == 0 else "right"] = description

        # Layout in grid (2 columns)
        col += 1
        if col >= num_columns:
            col = 0
            row += 1

    # Add legend text to the right of the grid
    legend_x = margin + grid_width + legend_spacing  # Positioned with margin and spacing
    text_height = 700  # Reduced from 1000
    line_spacing = 1000  # Reduced from 1500, spacing between Left and Right labels

    for row_idx in sorted(row_descriptions.keys()):
        descriptions = row_descriptions[row_idx]
        # Calculate Y position for this row (middle of the row, with margin)
        row_y = margin + (row_idx + 1) * y_spacing - (y_spacing / 2)

        # Add "Left:" label
        if "left" in descriptions:
            msp.add_text(
                f"Left: {descriptions['left']}",
                dxfattribs={
                    "insert": (legend_x, row_y),
                    "height": text_height,
                }
            )

        # Add "Right:" label below Left
        if "right" in descriptions:
            msp.add_text(
                f"Right: {descriptions['right']}",
                dxfattribs={
                    "insert": (legend_x, row_y - line_spacing),
                    "height": text_height,
                }
            )

    # Save the DXF file
    output_path = Path(__file__).parent / "comprehensive_scale_test_compact.dxf"
    doc.saveas(output_path)
    print(f"Created: {output_path}")
    print(f"Block instances: {len(test_cases)}")
    print(f"Grid layout: {num_columns} columns x {num_rows} rows")
    print(f"Grid dimensions: {grid_width} x {grid_height} units")


if __name__ == "__main__":
    create_comprehensive_scale_test_compact()
