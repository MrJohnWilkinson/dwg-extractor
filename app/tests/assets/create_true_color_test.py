"""
Script to create a test DXF file with True Color (24-bit RGB) entities.

This creates test fixtures for validating True Color extraction.
The file includes entities with:
- True Colors set via entity.rgb (which sets group code 420 internally)
- LINE, TEXT, and MTEXT entities with True Colors
- Mix of True Colors and ACI colors on the same layer
- Specific RGB values from the bug report: (124, 82, 165) and (0, 165, 165)

True Colors are stored in DXF as:
- Group code 420: 24-bit packed integer where R << 16 | G << 8 | B
- Accessible via entity.dxf.true_color or entity.rgb properties

Expected behavior after fix:
- All True Color entities should have their RGB values extracted
- Both True Color and ACI color entities should coexist correctly
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create layers - one with ACI color, one with True Color
doc.layers.add("TRUE_COLOR_LAYER", color=7)  # White (ACI)
doc.layers.add("ACI_COLOR_LAYER", color=1)  # Red (ACI)
doc.layers.add("MIXED_LAYER", color=7)  # White (ACI)

# Scenario 1: LINE with True Color (124, 82, 165) - purple shade from bug report
line1 = msp.add_line(
    start=(0, 0),
    end=(100, 0),
    dxfattribs={
        "layer": "TRUE_COLOR_LAYER",
    },
)
line1.rgb = (124, 82, 165)
# Expected RGB: (124, 82, 165)

# Scenario 2: LINE with True Color (0, 165, 165) - cyan shade from bug report
line2 = msp.add_line(
    start=(0, 10),
    end=(100, 10),
    dxfattribs={
        "layer": "TRUE_COLOR_LAYER",
    },
)
line2.rgb = (0, 165, 165)
# Expected RGB: (0, 165, 165)

# Scenario 3: TEXT with True Color
text1 = msp.add_text(
    "TRUE COLOR TEXT",
    dxfattribs={
        "layer": "TRUE_COLOR_LAYER",
        "insert": (0, 20),
        "height": 2.5,
    },
)
text1.rgb = (255, 128, 0)  # Orange
# Expected RGB: (255, 128, 0)

# Scenario 4: MTEXT with True Color
mtext1 = msp.add_mtext(
    "TRUE COLOR MTEXT",
    dxfattribs={
        "layer": "TRUE_COLOR_LAYER",
        "insert": (0, 30),
        "char_height": 2.5,
    },
)
mtext1.rgb = (128, 0, 255)  # Purple
# Expected RGB: (128, 0, 255)

# Scenario 5: LINE with ACI color (for comparison/regression testing)
line3 = msp.add_line(
    start=(0, 40),
    end=(100, 40),
    dxfattribs={
        "layer": "ACI_COLOR_LAYER",
        "color": 1,  # Red (ACI index 1)
    },
)
# Expected RGB: (255, 0, 0) - ACI red

# Scenario 6: TEXT with ACI color (for comparison)
text2 = msp.add_text(
    "ACI COLOR TEXT",
    dxfattribs={
        "layer": "ACI_COLOR_LAYER",
        "insert": (0, 50),
        "height": 2.5,
        "color": 3,  # Green (ACI index 3)
    },
)
# Expected RGB: (0, 255, 0) - ACI green

# Scenario 7: Mix of True Color and ACI on same layer
# True Color entity
line4 = msp.add_line(
    start=(0, 60),
    end=(100, 60),
    dxfattribs={
        "layer": "MIXED_LAYER",
    },
)
line4.rgb = (100, 200, 150)  # Custom green
# Expected RGB: (100, 200, 150)

# ACI entity on same layer
line5 = msp.add_line(
    start=(0, 70),
    end=(100, 70),
    dxfattribs={
        "layer": "MIXED_LAYER",
        "color": 5,  # Blue (ACI index 5)
    },
)
# Expected RGB: (0, 0, 255) - ACI blue

# Scenario 8: Another True Color TEXT for annotation testing
text3 = msp.add_text(
    "ANNOTATION WITH TRUE COLOR",
    dxfattribs={
        "layer": "MIXED_LAYER",
        "insert": (0, 80),
        "height": 2.5,
    },
)
text3.rgb = (200, 100, 50)  # Brownish
# Expected RGB: (200, 100, 50)

# Scenario 9: True Color on ByLayer entity (True Color overrides ByLayer)
line6 = msp.add_line(
    start=(0, 90),
    end=(100, 90),
    dxfattribs={
        "layer": "TRUE_COLOR_LAYER",
        "color": 256,  # ByLayer
    },
)
line6.rgb = (50, 150, 250)  # Light blue
# Expected RGB: (50, 150, 250) - True Color should override ByLayer

# Scenario 10: MTEXT with True Color for color analysis testing
mtext2 = msp.add_mtext(
    "COLOR ANALYSIS MTEXT",
    dxfattribs={
        "layer": "MIXED_LAYER",
        "insert": (0, 100),
        "char_height": 2.5,
    },
)
mtext2.rgb = (255, 200, 100)  # Peach
# Expected RGB: (255, 200, 100)

# Save DXF file
doc.saveas("app/tests/assets/true_color_test.dxf")
print("Created app/tests/assets/true_color_test.dxf with True Color scenarios")
print("\nExpected RGB values for each entity:")
print("1. LINE (124, 82, 165) - True Color purple")
print("2. LINE (0, 165, 165) - True Color cyan")
print("3. TEXT (255, 128, 0) - True Color orange")
print("4. MTEXT (128, 0, 255) - True Color purple")
print("5. LINE (255, 0, 0) - ACI red (index 1)")
print("6. TEXT (0, 255, 0) - ACI green (index 3)")
print("7. LINE (100, 200, 150) - True Color on MIXED_LAYER")
print("8. LINE (0, 0, 255) - ACI blue (index 5) on MIXED_LAYER")
print("9. TEXT (200, 100, 50) - True Color brownish annotation")
print("10. LINE (50, 150, 250) - True Color overrides ByLayer")
print("11. MTEXT (255, 200, 100) - True Color peach for color analysis")
