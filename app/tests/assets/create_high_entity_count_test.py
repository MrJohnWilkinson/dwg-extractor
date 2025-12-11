"""
Script to create a test DXF file with high entity count blocks.

This file is used for testing ENTITY_COUNT_THRESHOLD (1000) protection:
- HIGH_ENTITY_COUNT: 1500 LINE entities (exceeds threshold)
- LOW_ENTITY_COUNT: 500 LINE entities (under threshold)
- EXACTLY_ENTITY_THRESHOLD: Exactly 1000 entities (boundary test)
- JUST_OVER_ENTITY_THRESHOLD: 1001 entities (first to be skipped)
"""

import ezdxf


# Create a new DXF document
doc = ezdxf.new("R2010")

# Block 1: HIGH_ENTITY_COUNT - 1500 simple LINE entities (exceeds threshold of 1000)
block_high = doc.blocks.new(name="HIGH_ENTITY_COUNT")
for i in range(1500):
    x = (i % 50) * 10
    y = (i // 50) * 10
    block_high.add_line((x, y), (x + 5, y))

# Block 2: LOW_ENTITY_COUNT - 500 simple LINE entities (under threshold)
block_low = doc.blocks.new(name="LOW_ENTITY_COUNT")
for i in range(500):
    x = (i % 25) * 10
    y = (i // 25) * 10
    block_low.add_line((x, y), (x + 5, y))

# Block 3: EXACTLY_ENTITY_THRESHOLD - Exactly 1000 entities (boundary test)
block_exact = doc.blocks.new(name="EXACTLY_ENTITY_THRESHOLD")
for i in range(1000):
    x = (i % 40) * 10
    y = (i // 40) * 10
    block_exact.add_line((x, y), (x + 5, y))

# Block 4: JUST_OVER_ENTITY_THRESHOLD - 1001 entities (first to be skipped)
block_over = doc.blocks.new(name="JUST_OVER_ENTITY_THRESHOLD")
for i in range(1001):
    x = (i % 40) * 10
    y = (i // 40) * 10
    block_over.add_line((x, y), (x + 5, y))

# Add block references to modelspace
msp = doc.modelspace()
msp.add_blockref("HIGH_ENTITY_COUNT", (0, 0))
msp.add_blockref("LOW_ENTITY_COUNT", (600, 0))
msp.add_blockref("EXACTLY_ENTITY_THRESHOLD", (0, 400))
msp.add_blockref("JUST_OVER_ENTITY_THRESHOLD", (600, 400))

# Save the file
doc.saveas("app/tests/assets/high_entity_count_test.dxf")
print("Created high_entity_count_test.dxf successfully")

# Print entity counts for verification
print(f"HIGH_ENTITY_COUNT block entity count: {sum(1 for _ in block_high)}")
print(f"LOW_ENTITY_COUNT block entity count: {sum(1 for _ in block_low)}")
print(f"EXACTLY_ENTITY_THRESHOLD block entity count: {sum(1 for _ in block_exact)}")
print(f"JUST_OVER_ENTITY_THRESHOLD block entity count: {sum(1 for _ in block_over)}")
