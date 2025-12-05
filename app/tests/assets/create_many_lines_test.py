"""
Generate a test DXF file with many LINE segments for testing threshold behavior.

This script creates a block with 250+ LINE segments forming a complex interconnected
pattern that would cause exponential DFS exploration if not thresholded.
"""

import ezdxf


def create_many_lines_test() -> None:
    """Create a test DXF file with many LINE segments."""
    doc = ezdxf.new()
    msp = doc.modelspace()

    # Create a block with many LINE segments
    block = doc.blocks.new(name="MANY_LINES_BLOCK")

    # Create a grid pattern with 250+ lines
    # This creates a dense interconnected graph that would be computationally expensive
    # to analyze for cycles without the threshold protection
    grid_size = 16  # 16x16 grid creates 2*17*16 = 544 lines
    spacing = 10.0

    line_count = 0

    # Horizontal lines
    for row in range(grid_size + 1):
        y = row * spacing
        for col in range(grid_size):
            x_start = col * spacing
            x_end = (col + 1) * spacing
            block.add_line((x_start, y), (x_end, y))
            line_count += 1

    # Vertical lines
    for col in range(grid_size + 1):
        x = col * spacing
        for row in range(grid_size):
            y_start = row * spacing
            y_end = (row + 1) * spacing
            block.add_line((x, y_start), (x, y_end))
            line_count += 1

    # Add some diagonal lines to make it even more complex
    for i in range(grid_size):
        x = i * spacing
        block.add_line((x, 0), (x + spacing, spacing))
        block.add_line((x, spacing), (x + spacing, 0))
        line_count += 2

    print(f"Created block 'MANY_LINES_BLOCK' with {line_count} LINE segments")

    # Insert the block into modelspace
    msp.add_blockref("MANY_LINES_BLOCK", (0, 0))

    # Save the file
    output_path = "app/tests/assets/many_lines_test.dxf"
    doc.saveas(output_path)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    create_many_lines_test()
