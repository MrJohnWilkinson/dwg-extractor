"""
Script to create a test DXF file with TEXT and MTEXT annotation scenarios.

This creates test fixtures for validating the Annotations Analysis feature.
The file includes:
- TEXT entities with different colors (direct RGB, ByLayer, ACI index)
- MTEXT entities with different colors
- Same text content on different layers
- Same text content with different colors
- Duplicate annotations (same content, type, layer, color)
- Special characters and unicode in text content
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create layers with different colors
doc.layers.add("LAYER_RED", color=1)  # ACI 1 = red
doc.layers.add("LAYER_GREEN", color=3)  # ACI 3 = green
doc.layers.add("LAYER_BLUE", color=5)  # ACI 5 = blue
doc.layers.add("LAYER_WHITE", color=7)  # ACI 7 = white

# Scenario 1: TEXT entity with direct RGB color
text1 = msp.add_text(
    "Sample Text 1",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 0),
        "height": 2.5,
    },
)
text1.rgb = (255, 0, 0)  # Direct red RGB

# Scenario 2: TEXT entity with ByLayer color (should resolve to layer color)
text2 = msp.add_text(
    "Sample Text 2",
    dxfattribs={
        "layer": "LAYER_GREEN",
        "insert": (0, 10),
        "height": 2.5,
        "color": 256,  # ByLayer
    },
)

# Scenario 3: TEXT entity with ACI color index
text3 = msp.add_text(
    "Sample Text 3",
    dxfattribs={
        "layer": "LAYER_BLUE",
        "insert": (0, 20),
        "height": 2.5,
        "color": 5,  # ACI blue
    },
)

# Scenario 4: MTEXT entity with direct RGB color
mtext1 = msp.add_mtext(
    "This is a multiline\\Ptext annotation",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (50, 0),
        "char_height": 2.5,
    },
)
mtext1.rgb = (0, 255, 0)  # Direct green RGB

# Scenario 5: MTEXT entity with ByLayer color
mtext2 = msp.add_mtext(
    "Another MTEXT",
    dxfattribs={
        "layer": "LAYER_BLUE",
        "insert": (50, 10),
        "char_height": 2.5,
        "color": 256,  # ByLayer
    },
)

# Scenario 6: Duplicate annotations (same text, layer, color) - should count as 2
text4 = msp.add_text(
    "Duplicate Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 30),
        "height": 2.5,
        "color": 1,  # ACI red
    },
)
text5 = msp.add_text(
    "Duplicate Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 40),
        "height": 2.5,
        "color": 1,  # ACI red - same as text4
    },
)

# Scenario 7: Same text content but different layers (should be separate groups)
text6 = msp.add_text(
    "Cross Layer Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 50),
        "height": 2.5,
        "color": 1,
    },
)
text7 = msp.add_text(
    "Cross Layer Text",
    dxfattribs={
        "layer": "LAYER_GREEN",
        "insert": (0, 60),
        "height": 2.5,
        "color": 3,
    },
)

# Scenario 8: Same text content but different colors on same layer (should be separate)
text8 = msp.add_text(
    "Multi Color Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 70),
        "height": 2.5,
        "color": 1,  # Red
    },
)
text9 = msp.add_text(
    "Multi Color Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 80),
        "height": 2.5,
        "color": 3,  # Green - different color
    },
)

# Scenario 9: TEXT vs MTEXT with same content (should be separate groups)
text10 = msp.add_text(
    "Same Content Different Type",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 90),
        "height": 2.5,
        "color": 1,
    },
)
mtext3 = msp.add_mtext(
    "Same Content Different Type",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (50, 90),
        "char_height": 2.5,
        "color": 1,
    },
)

# Scenario 10: Special characters and unicode
text11 = msp.add_text(
    "Special: @#$%^&*()_+{}[]|\\:;\"'<>?,./",
    dxfattribs={
        "layer": "LAYER_WHITE",
        "insert": (0, 100),
        "height": 2.5,
        "color": 7,
    },
)

mtext4 = msp.add_mtext(
    "Unicode: \u00b0\u00b1\u00b2\u00b3 \u03b1\u03b2\u03b3",
    dxfattribs={
        "layer": "LAYER_WHITE",
        "insert": (50, 100),
        "char_height": 2.5,
        "color": 7,
    },
)

# Scenario 11: ByBlock color (should default to white)
text12 = msp.add_text(
    "ByBlock Color Text",
    dxfattribs={
        "layer": "LAYER_RED",
        "insert": (0, 110),
        "height": 2.5,
        "color": 0,  # ByBlock
    },
)

# Save DXF file
doc.saveas("app/tests/assets/annotation_test.dxf")
print("Created app/tests/assets/annotation_test.dxf with annotation scenarios")
print("\nExpected annotation groups:")
print("- 'Sample Text 1' (TEXT, LAYER_RED, RGB 255,0,0) = 1")
print("- 'Sample Text 2' (TEXT, LAYER_GREEN, ByLayer -> ACI 3) = 1")
print("- 'Sample Text 3' (TEXT, LAYER_BLUE, ACI 5) = 1")
print("- 'This is a multiline\\ntext annotation' (MTEXT, LAYER_RED, RGB 0,255,0) = 1")
print("- 'Another MTEXT' (MTEXT, LAYER_BLUE, ByLayer -> ACI 5) = 1")
print("- 'Duplicate Text' (TEXT, LAYER_RED, ACI 1) = 2 *** COUNT = 2")
print("- 'Cross Layer Text' (TEXT, LAYER_RED, ACI 1) = 1")
print("- 'Cross Layer Text' (TEXT, LAYER_GREEN, ACI 3) = 1")
print("- 'Multi Color Text' (TEXT, LAYER_RED, ACI 1) = 1")
print("- 'Multi Color Text' (TEXT, LAYER_RED, ACI 3) = 1")
print("- 'Same Content Different Type' (TEXT, LAYER_RED, ACI 1) = 1")
print("- 'Same Content Different Type' (MTEXT, LAYER_RED, ACI 1) = 1")
print("- 'Special: @#$%^&*()_+{}[]|\\:;\"'<>?,./' (TEXT, LAYER_WHITE, ACI 7) = 1")
print("- 'Unicode: °±²³ αβγ' (MTEXT, LAYER_WHITE, ACI 7) = 1")
print("- 'ByBlock Color Text' (TEXT, LAYER_RED, ByBlock -> white 255,255,255) = 1")
