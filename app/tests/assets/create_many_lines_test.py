"""
Script to create a test DXF file with many LINE segments.

This file is used for testing LINE segment threshold protection:
- MANY_LINES: 5500+ LINE segments (grid pattern) to exceed LINE_SEGMENT_THRESHOLD
- FEW_LINES: Simple rectangle with <50 LINE segments
"""

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block 1: MANY_LINES - Grid pattern with 5500+ LINE segments
# This exceeds LINE_SEGMENT_THRESHOLD (5000) to test threshold skip
block_many = doc.blocks.new(name="MANY_LINES")

# Create a 75x75 grid of lines to exceed 5000 segments
# Total: 76 horizontal + 76 vertical + 75*2 diagonal + 5000 extra = 5302+ segments
grid_size = 75
spacing = 10

# Horizontal lines (76 lines)
for i in range(grid_size + 1):
    y = i * spacing
    block_many.add_line((0, y), (grid_size * spacing, y))

# Vertical lines (76 lines)
for i in range(grid_size + 1):
    x = i * spacing
    block_many.add_line((x, 0), (x, grid_size * spacing))

# Add some diagonal lines to increase count (150 lines)
for i in range(grid_size):
    x = i * spacing
    y = i * spacing
    block_many.add_line((x, y), (x + spacing, y + spacing))
    block_many.add_line((x + spacing, y), (x, y + spacing))

# Add extra lines to ensure we're well over 5000
for i in range(5000):
    x = (i % 100) * spacing
    y = (i // 100) * spacing
    block_many.add_line((x, y), (x + 5, y + 5))

# Block 2: FEW_LINES - Simple rectangle with few LINE segments
block_few = doc.blocks.new(name="FEW_LINES")
# Simple rectangle using 4 LINE segments
block_few.add_line((0, 0), (100, 0))
block_few.add_line((100, 0), (100, 50))
block_few.add_line((100, 50), (0, 50))
block_few.add_line((0, 50), (0, 0))
# Add a few more lines inside (still well under threshold)
block_few.add_line((10, 10), (90, 10))
block_few.add_line((90, 10), (90, 40))
block_few.add_line((90, 40), (10, 40))
block_few.add_line((10, 40), (10, 10))

# Block 3: EXACTLY_THRESHOLD - Exactly 5000 LINE segments
block_exact = doc.blocks.new(name="EXACTLY_THRESHOLD")
for i in range(5000):
    x = (i % 100) * 10
    y = (i // 100) * 10
    block_exact.add_line((x, y), (x + 5, y))

# Block 4: JUST_OVER_THRESHOLD - 5001 LINE segments
block_over = doc.blocks.new(name="JUST_OVER_THRESHOLD")
for i in range(5001):
    x = (i % 100) * 10
    y = (i // 100) * 10
    block_over.add_line((x, y), (x + 5, y))

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("MANY_LINES", (0, 0))
msp.add_blockref("FEW_LINES", (300, 0))
msp.add_blockref("EXACTLY_THRESHOLD", (0, 300))
msp.add_blockref("JUST_OVER_THRESHOLD", (300, 300))

# Save the file
doc.saveas("app/tests/assets/many_lines_test.dxf")
print("Created many_lines_test.dxf successfully")

# Print line counts for verification
print(
    f"MANY_LINES block line count: {sum(1 for e in block_many if e.dxftype() == 'LINE')}"
)
print(
    f"FEW_LINES block line count: {sum(1 for e in block_few if e.dxftype() == 'LINE')}"
)
print(
    f"EXACTLY_THRESHOLD block line count: {sum(1 for e in block_exact if e.dxftype() == 'LINE')}"
)
print(
    f"JUST_OVER_THRESHOLD block line count: {sum(1 for e in block_over if e.dxftype() == 'LINE')}"
)
