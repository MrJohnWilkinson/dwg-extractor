"""
Script to create a test DXF file with nested block scenarios.

This creates test fixtures for validating nested block detection functionality:
- OUTER_BLOCK: Contains INSERT references to INNER_BLOCK and MULTI_PARENT_BLOCK
- INNER_BLOCK: Nested only (no modelspace insertion)
- STANDALONE_BLOCK: Inserted in modelspace, not nested in any other block
- UNUSED_BLOCK: Defined but never inserted anywhere
- MULTI_PARENT_BLOCK: Inserted in both OUTER_BLOCK and SECOND_OUTER, also in modelspace
- SECOND_OUTER: Contains INSERT of MULTI_PARENT_BLOCK

Block nesting scenarios covered:
1. Nested-only blocks (never inserted in modelspace)
2. Multi-parent blocks (nested in multiple parent blocks)
3. Unused blocks (defined but never inserted)
4. Standalone blocks (inserted in modelspace, not nested)
5. Blocks inserted both in modelspace and nested in other blocks
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create INNER_BLOCK - will be nested only (no modelspace insertion)
inner_block = doc.blocks.new(name="INNER_BLOCK")
inner_block.add_lwpolyline([(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)])
inner_block.add_circle(center=(2.5, 2.5), radius=1.5)

# Create MULTI_PARENT_BLOCK - will be nested in multiple parents AND in modelspace
multi_parent_block = doc.blocks.new(name="MULTI_PARENT_BLOCK")
multi_parent_block.add_lwpolyline([(0, 0), (8, 0), (8, 4), (0, 4), (0, 0)])
multi_parent_block.add_line((0, 2), (8, 2))

# Create OUTER_BLOCK - contains INNER_BLOCK and MULTI_PARENT_BLOCK
outer_block = doc.blocks.new(name="OUTER_BLOCK")
outer_block.add_lwpolyline([(0, 0), (30, 0), (30, 20), (0, 20), (0, 0)])
# Nest INNER_BLOCK inside OUTER_BLOCK
outer_block.add_blockref("INNER_BLOCK", (5, 5))
outer_block.add_blockref("INNER_BLOCK", (20, 5))
# Nest MULTI_PARENT_BLOCK inside OUTER_BLOCK
outer_block.add_blockref("MULTI_PARENT_BLOCK", (5, 12))

# Create SECOND_OUTER - also contains MULTI_PARENT_BLOCK (to test multi-parent)
second_outer = doc.blocks.new(name="SECOND_OUTER")
second_outer.add_lwpolyline([(0, 0), (25, 0), (25, 15), (0, 15), (0, 0)])
# Nest MULTI_PARENT_BLOCK inside SECOND_OUTER
second_outer.add_blockref("MULTI_PARENT_BLOCK", (8, 6))

# Create STANDALONE_BLOCK - inserted in modelspace only, not nested
standalone_block = doc.blocks.new(name="STANDALONE_BLOCK")
standalone_block.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
standalone_block.add_line((0, 0), (10, 10))
standalone_block.add_line((10, 0), (0, 10))

# Create UNUSED_BLOCK - defined but never inserted anywhere
unused_block = doc.blocks.new(name="UNUSED_BLOCK")
unused_block.add_circle(center=(5, 5), radius=5)
unused_block.add_text("UNUSED", dxfattribs={"height": 2, "insert": (2, 4)})

# Insert blocks in modelspace

# OUTER_BLOCK - inserted in modelspace (contains INNER_BLOCK and MULTI_PARENT_BLOCK)
msp.add_blockref("OUTER_BLOCK", (0, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("OUTER_BLOCK", (50, 0), dxfattribs={"layer": "LAYER_B"})

# SECOND_OUTER - inserted in modelspace (contains MULTI_PARENT_BLOCK)
msp.add_blockref("SECOND_OUTER", (0, 50), dxfattribs={"layer": "LAYER_A"})

# STANDALONE_BLOCK - inserted in modelspace only
msp.add_blockref("STANDALONE_BLOCK", (100, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("STANDALONE_BLOCK", (120, 0), dxfattribs={"layer": "LAYER_A"})
msp.add_blockref("STANDALONE_BLOCK", (100, 20), dxfattribs={"layer": "LAYER_B"})

# MULTI_PARENT_BLOCK - also inserted directly in modelspace (in addition to nested)
msp.add_blockref("MULTI_PARENT_BLOCK", (150, 0), dxfattribs={"layer": "LAYER_C"})

# Note: INNER_BLOCK is NOT inserted in modelspace (nested only)
# Note: UNUSED_BLOCK is NOT inserted anywhere

# Save DXF file
doc.saveas("app/tests/assets/nested_block_test.dxf")
print("Created app/tests/assets/nested_block_test.dxf with nested block scenarios")
print("\n" + "=" * 70)
print("BLOCK DEFINITIONS SUMMARY")
print("=" * 70)
print("\nUser-defined blocks created:")
print("  1. OUTER_BLOCK      - 4 entities (1 polyline + 3 block refs)")
print("  2. INNER_BLOCK      - 2 entities (1 polyline + 1 circle)")
print("  3. STANDALONE_BLOCK - 3 entities (1 polyline + 2 lines)")
print("  4. UNUSED_BLOCK     - 2 entities (1 circle + 1 text)")
print("  5. MULTI_PARENT_BLOCK - 2 entities (1 polyline + 1 line)")
print("  6. SECOND_OUTER     - 2 entities (1 polyline + 1 block ref)")
print("\n" + "=" * 70)
print("EXPECTED NESTED BLOCK DETECTION RESULTS")
print("=" * 70)
print("\nBlock Insertion Status:")
print("  - OUTER_BLOCK:       'Inserted' (2 modelspace insertions)")
print("  - INNER_BLOCK:       'Nested Only' (0 modelspace, nested in OUTER_BLOCK)")
print("  - STANDALONE_BLOCK:  'Inserted' (3 modelspace insertions)")
print("  - UNUSED_BLOCK:      'Unused' (0 insertions anywhere)")
print("  - MULTI_PARENT_BLOCK:'Inserted' (1 modelspace + nested in 2 parents)")
print("  - SECOND_OUTER:      'Inserted' (1 modelspace insertion)")
print("\nBlock Nesting Status (block_is_nested):")
print("  - OUTER_BLOCK:       False (not nested in any block)")
print("  - INNER_BLOCK:       True  (nested in OUTER_BLOCK)")
print("  - STANDALONE_BLOCK:  False (not nested in any block)")
print("  - UNUSED_BLOCK:      False (not nested in any block)")
print("  - MULTI_PARENT_BLOCK:True  (nested in OUTER_BLOCK, SECOND_OUTER)")
print("  - SECOND_OUTER:      False (not nested in any block)")
print("\nBlock Nested Parent Names:")
print("  - OUTER_BLOCK:       []")
print("  - INNER_BLOCK:       ['OUTER_BLOCK']")
print("  - STANDALONE_BLOCK:  []")
print("  - UNUSED_BLOCK:      []")
print("  - MULTI_PARENT_BLOCK:['OUTER_BLOCK', 'SECOND_OUTER']")
print("  - SECOND_OUTER:      []")
print("\n" + "=" * 70)
print("MODELSPACE INSERTIONS")
print("=" * 70)
print("\n  OUTER_BLOCK:        2 insertions (LAYER_A=1, LAYER_B=1)")
print("  SECOND_OUTER:       1 insertion  (LAYER_A=1)")
print("  STANDALONE_BLOCK:   3 insertions (LAYER_A=2, LAYER_B=1)")
print("  MULTI_PARENT_BLOCK: 1 insertion  (LAYER_C=1)")
print("  INNER_BLOCK:        0 insertions (nested only)")
print("  UNUSED_BLOCK:       0 insertions (unused)")
