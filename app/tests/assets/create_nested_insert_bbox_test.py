"""
Script to create a test DXF file with nested INSERT scenarios for bounding box testing.

This creates test fixtures for validating nested INSERT geometry expansion:
- INNER_BOX: Simple rectangle from (0,0) to (10,10)
- OUTER_SIMPLE: Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (5,5)
- OUTER_SCALED: Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (5,5) with scale (2,2)
- OUTER_ROTATED: Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (25,15) with 45 degree rotation
- CIRCULAR_A: Rectangle (0,0) to (20,20) + INSERT of CIRCULAR_B at (5,5)
- CIRCULAR_B: Rectangle (0,0) to (10,10) + INSERT of CIRCULAR_A at (2,2) (circular reference)

Scenarios covered:
1. Simple nesting (no transform)
2. Scaled nested INSERT
3. Rotated nested INSERT
4. Circular reference protection
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create INNER_BOX - basic rectangle for nesting tests
inner_box = doc.blocks.new(name="INNER_BOX")
inner_box.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)

# Create OUTER_SIMPLE - contains INNER_BOX at position (5,5) with no transform
outer_simple = doc.blocks.new(name="OUTER_SIMPLE")
outer_simple.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)
outer_simple.add_blockref("INNER_BOX", (5, 5))

# Create OUTER_SCALED - contains INNER_BOX at position (5,5) with scale (2,2)
outer_scaled = doc.blocks.new(name="OUTER_SCALED")
outer_scaled.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)
outer_scaled.add_blockref(
    "INNER_BOX", (5, 5), dxfattribs={"xscale": 2.0, "yscale": 2.0}
)

# Create OUTER_ROTATED - contains INNER_BOX at position (25,15) with 45 degree rotation
outer_rotated = doc.blocks.new(name="OUTER_ROTATED")
outer_rotated.add_lwpolyline([(0, 0), (50, 0), (50, 30), (0, 30)], close=True)
outer_rotated.add_blockref("INNER_BOX", (25, 15), dxfattribs={"rotation": 45.0})

# Create CIRCULAR_A and CIRCULAR_B - circular reference for testing infinite loop protection
circular_a = doc.blocks.new(name="CIRCULAR_A")
circular_a.add_lwpolyline([(0, 0), (20, 0), (20, 20), (0, 20)], close=True)
# Note: We add CIRCULAR_B reference AFTER creating CIRCULAR_B
# to ensure both blocks exist

circular_b = doc.blocks.new(name="CIRCULAR_B")
circular_b.add_lwpolyline([(0, 0), (10, 0), (10, 10), (0, 10)], close=True)
# Add circular reference: CIRCULAR_B references CIRCULAR_A
circular_b.add_blockref("CIRCULAR_A", (2, 2))

# Now add CIRCULAR_A's reference to CIRCULAR_B
circular_a.add_blockref("CIRCULAR_B", (5, 5))

# Create OUTER_COMBO - contains INNER_BOX with both scale and rotation
outer_combo = doc.blocks.new(name="OUTER_COMBO")
outer_combo.add_lwpolyline([(0, 0), (60, 0), (60, 40), (0, 40)], close=True)
outer_combo.add_blockref(
    "INNER_BOX", (30, 20), dxfattribs={"xscale": 1.5, "yscale": 1.5, "rotation": 30.0}
)

# Create DEEP_OUTER - contains OUTER_SIMPLE to test multi-level nesting
deep_outer = doc.blocks.new(name="DEEP_OUTER")
deep_outer.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)], close=True)
deep_outer.add_blockref("OUTER_SIMPLE", (10, 10))

# Insert blocks in modelspace for visualization
msp.add_blockref("OUTER_SIMPLE", (0, 0))
msp.add_blockref("OUTER_SCALED", (0, 50))
msp.add_blockref("OUTER_ROTATED", (0, 100))
msp.add_blockref("CIRCULAR_A", (100, 0))
msp.add_blockref("OUTER_COMBO", (100, 50))
msp.add_blockref("DEEP_OUTER", (0, 150))

# Save DXF file
doc.saveas("app/tests/assets/nested_insert_bbox_test.dxf")
print(
    "Created app/tests/assets/nested_insert_bbox_test.dxf with nested INSERT scenarios"
)
print("\n" + "=" * 70)
print("BLOCK DEFINITIONS SUMMARY")
print("=" * 70)
print("\nUser-defined blocks created:")
print("  1. INNER_BOX        - Rectangle (0,0) to (10,10)")
print(
    "  2. OUTER_SIMPLE     - Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (5,5)"
)
print(
    "  3. OUTER_SCALED     - Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (5,5) scale=(2,2)"
)
print(
    "  4. OUTER_ROTATED    - Rectangle (0,0) to (50,30) + INSERT of INNER_BOX at (25,15) rotation=45"
)
print(
    "  5. CIRCULAR_A       - Rectangle (0,0) to (20,20) + INSERT of CIRCULAR_B at (5,5)"
)
print(
    "  6. CIRCULAR_B       - Rectangle (0,0) to (10,10) + INSERT of CIRCULAR_A at (2,2)"
)
print(
    "  7. OUTER_COMBO      - Rectangle (0,0) to (60,40) + INSERT of INNER_BOX scale=(1.5,1.5) rotation=30"
)
print(
    "  8. DEEP_OUTER       - Rectangle (0,0) to (100,60) + INSERT of OUTER_SIMPLE at (10,10)"
)
print("\n" + "=" * 70)
print("EXPECTED BOUNDING BOX RESULTS")
print("=" * 70)
print("\nWithout nested expansion (current behavior):")
print("  - INNER_BOX:     (0, 0, 10, 10)")
print("  - OUTER_SIMPLE:  (0, 0, 50, 30)")
print("  - OUTER_SCALED:  (0, 0, 50, 30)")
print("  - OUTER_ROTATED: (0, 0, 50, 30)")
print("\nWith nested expansion (new behavior):")
print("  - INNER_BOX:     (0, 0, 10, 10) - no change")
print(
    "  - OUTER_SIMPLE:  (0, 0, 50, 30) - INNER_BOX at (5,5)+(10,10) = (15,15) within bbox"
)
print(
    "  - OUTER_SCALED:  (0, 0, 50, 30) - INNER_BOX scaled 2x at (5,5)+(20,20) = (25,25) within bbox"
)
print(
    "  - OUTER_ROTATED: varies - INNER_BOX rotated 45 may extend outside original bbox"
)
print("\nCircular reference test:")
print("  - CIRCULAR_A should compute bbox without infinite loop")
print("  - CIRCULAR_B should compute bbox without infinite loop")
