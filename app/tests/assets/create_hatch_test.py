"""
Script to create a test DXF file with HATCH entities.

This creates test fixtures for validating HATCH extraction in color analysis.
The file includes:
- HATCH entities with different ACI colors on different layers
- HATCH entities with True Color
- Multiple hatches with same color/layer (to test aggregation)
- Mix of HATCH with other entity types for integration testing

Expected behavior:
- HATCH entities should appear in color_analysis_data with entity_type="Hatches"
- HATCH entities should be grouped by (color_r, color_g, color_b, color_aci, layer_name, "Hatches")
- Entity count should reflect aggregation of multiple hatches with same color/layer
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create layers for testing
doc.layers.add("HATCH_LAYER_A", color=1)  # Red (ACI)
doc.layers.add("HATCH_LAYER_B", color=3)  # Green (ACI)
doc.layers.add("MIXED_LAYER", color=7)  # White (ACI)

# Scenario 1: HATCH with ACI color 1 (red) on HATCH_LAYER_A
# First hatch with simple rectangular boundary
hatch1 = msp.add_hatch(
    color=1,  # Red ACI
    dxfattribs={"layer": "HATCH_LAYER_A"},
)
hatch1.paths.add_polyline_path([(0, 0), (10, 0), (10, 10), (0, 10)], is_closed=True)
# Expected: entity_type="Hatches", color_aci=1, layer="HATCH_LAYER_A"

# Scenario 2: Another HATCH with same color/layer (should aggregate with hatch1)
hatch2 = msp.add_hatch(
    color=1,  # Red ACI
    dxfattribs={"layer": "HATCH_LAYER_A"},
)
hatch2.paths.add_polyline_path([(20, 0), (30, 0), (30, 10), (20, 10)], is_closed=True)
# Expected: Aggregated with hatch1, entity_count=2

# Scenario 3: Third HATCH with same color/layer (should aggregate)
hatch3 = msp.add_hatch(
    color=1,  # Red ACI
    dxfattribs={"layer": "HATCH_LAYER_A"},
)
hatch3.paths.add_polyline_path([(40, 0), (50, 0), (50, 10), (40, 10)], is_closed=True)
# Expected: Aggregated with hatch1 and hatch2, entity_count=3

# Scenario 4: HATCH with different ACI color 3 (green) on HATCH_LAYER_B
hatch4 = msp.add_hatch(
    color=3,  # Green ACI
    dxfattribs={"layer": "HATCH_LAYER_B"},
)
hatch4.paths.add_polyline_path([(0, 20), (10, 20), (10, 30), (0, 30)], is_closed=True)
# Expected: entity_type="Hatches", color_aci=3, layer="HATCH_LAYER_B"

# Scenario 5: HATCH with True Color
hatch5 = msp.add_hatch(
    dxfattribs={"layer": "MIXED_LAYER"},
)
hatch5.paths.add_polyline_path([(0, 40), (10, 40), (10, 50), (0, 50)], is_closed=True)
hatch5.rgb = (124, 82, 165)  # True Color purple
# Expected: entity_type="Hatches", color_aci=None, RGB=(124, 82, 165)

# Scenario 6: Another HATCH with same True Color (should aggregate)
hatch6 = msp.add_hatch(
    dxfattribs={"layer": "MIXED_LAYER"},
)
hatch6.paths.add_polyline_path([(20, 40), (30, 40), (30, 50), (20, 50)], is_closed=True)
hatch6.rgb = (124, 82, 165)  # Same True Color purple
# Expected: Aggregated with hatch5, entity_count=2

# Scenario 7: HATCH with ByLayer color (256)
hatch7 = msp.add_hatch(
    color=256,  # ByLayer
    dxfattribs={"layer": "HATCH_LAYER_B"},
)
hatch7.paths.add_polyline_path([(20, 20), (30, 20), (30, 30), (20, 30)], is_closed=True)
# Expected: Should resolve to HATCH_LAYER_B's ACI color (3)

# Scenario 8: HATCH with ByBlock color (0) - should default to white
hatch8 = msp.add_hatch(
    color=0,  # ByBlock
    dxfattribs={"layer": "MIXED_LAYER"},
)
hatch8.paths.add_polyline_path([(40, 40), (50, 40), (50, 50), (40, 50)], is_closed=True)
# Expected: RGB=(255, 255, 255), color_aci=0

# Scenario 9: Add a LINE for integration testing (mixed entity types)
line1 = msp.add_line(
    start=(0, 60),
    end=(100, 60),
    dxfattribs={
        "layer": "MIXED_LAYER",
        "color": 1,  # Red ACI
    },
)
# Expected: entity_type="Lines", separate from Hatches

# Scenario 10: Add a POLYLINE for integration testing
msp.add_lwpolyline(
    [(0, 70), (10, 70), (10, 80), (0, 80)],
    dxfattribs={
        "layer": "MIXED_LAYER",
        "color": 3,  # Green ACI
    },
)
# Expected: entity_type="Polylines", separate from Hatches

# Scenario 11: Add TEXT for integration testing
text1 = msp.add_text(
    "TEST TEXT",
    dxfattribs={
        "layer": "MIXED_LAYER",
        "insert": (0, 90),
        "height": 2.5,
        "color": 5,  # Blue ACI
    },
)
# Expected: entity_type="TEXT", separate from Hatches

# Save DXF file
doc.saveas("app/tests/assets/hatch_test.dxf")
print("Created app/tests/assets/hatch_test.dxf with HATCH scenarios")
print("\nExpected records in color_analysis_data:")
print("1. Hatches on HATCH_LAYER_A with ACI 1 (red): count=3")
print("2. Hatches on HATCH_LAYER_B with ACI 3 (green): count=1")
print("3. Hatches on MIXED_LAYER with True Color (124, 82, 165): count=2")
print("4. Hatches on HATCH_LAYER_B with ByLayer (ACI 3): count=1")
print("5. Hatches on MIXED_LAYER with ByBlock (white): count=1")
print("6. Lines on MIXED_LAYER with ACI 1 (red): count=1")
print("7. Polylines on MIXED_LAYER with ACI 3 (green): count=1")
print("8. TEXT on MIXED_LAYER with ACI 5 (blue): count=1")
