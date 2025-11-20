#!/usr/bin/env python3
"""
Generator script for empty_layers_test.dxf

Creates a DXF file with many layers to test that all layers from the layer table
are included in extraction results, even if they contain no entities.

Test characteristics:
- 60+ layers defined in the layer table
- Only a few layers contain entities (lines and block insertions)
- Many layers are empty (no entities)
- Tests layer_entity_counts and layer_block_insertion_counts completeness
"""

import ezdxf

# Create a new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Define 60+ layers - many will remain empty
layer_names = [
    # Layers with entities (will add content to these)
    "0",
    "Walls",
    "Furniture",
    "Electrical",
    "Plumbing",
    "Annotations",
    # Empty layers (defined but no entities)
    "Defpoints",
    "Fixture Name",
    "FPProfileCode",
    "HVAC",
    "Fire Protection",
    "Mechanical",
    "Structural",
    "Foundation",
    "Roof",
    "Windows",
    "Doors",
    "Ceiling",
    "Flooring",
    "Lighting",
    "Controls",
    "Data",
    "Telecom",
    "Security",
    "AV",
    "Casework",
    "Millwork",
    "Finishes",
    "Tile",
    "Paint",
    "Equipment",
    "Appliances",
    "Fixtures",
    "Hardware",
    "Accessories",
    "Signage",
    "Graphics",
    "Landscaping",
    "Site Work",
    "Grading",
    "Paving",
    "Curbs",
    "Sidewalks",
    "Parking",
    "Fencing",
    "Gates",
    "Irrigation",
    "Drainage",
    "Utilities",
    "Gas",
    "Water",
    "Sewer",
    "Storm",
    "Telecom Underground",
    "Power Underground",
    "Dimensions",
    "Text",
    "Hatching",
    "Reference",
    "Grid",
    "Symbols",
]

# Create all layers
for layer_name in layer_names:
    if layer_name not in doc.layers:
        doc.layers.add(layer_name)

# Create a simple block definition
block = doc.blocks.new(name="TestBlock")
block.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])

# Add entities only to specific layers
# Layer "Walls" - add some lines
msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "Walls"})
msp.add_line((10, 0), (10, 10), dxfattribs={"layer": "Walls"})
msp.add_line((10, 10), (0, 10), dxfattribs={"layer": "Walls"})
msp.add_line((0, 10), (0, 0), dxfattribs={"layer": "Walls"})

# Layer "Furniture" - add block insertions
msp.add_blockref("TestBlock", (2, 2), dxfattribs={"layer": "Furniture"})
msp.add_blockref("TestBlock", (5, 5), dxfattribs={"layer": "Furniture"})
msp.add_blockref("TestBlock", (8, 2), dxfattribs={"layer": "Furniture"})

# Layer "Electrical" - add a few lines
msp.add_line((0, 5), (10, 5), dxfattribs={"layer": "Electrical"})
msp.add_line((5, 0), (5, 10), dxfattribs={"layer": "Electrical"})

# Layer "Plumbing" - add a circle
msp.add_circle((5, 5), radius=2, dxfattribs={"layer": "Plumbing"})

# Layer "Annotations" - add text
msp.add_text("Test Drawing", dxfattribs={"layer": "Annotations"}).set_placement(
    (5, 12)
)

# Layer "0" (default layer) - add one line
msp.add_line((0, 0), (1, 1), dxfattribs={"layer": "0"})

# All other layers remain empty (defined but no entities)

# Save the DXF file
output_path = "app/tests/assets/empty_layers_test.dxf"
doc.saveas(output_path)
print(f"Created test file: {output_path}")
print(f"Total layers defined: {len(layer_names)}")
print(f"Layers with entities: 6 (0, Walls, Furniture, Electrical, Plumbing, Annotations)")
print(f"Empty layers: {len(layer_names) - 6}")
