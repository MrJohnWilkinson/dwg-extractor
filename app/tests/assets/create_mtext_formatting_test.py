"""
Script to create a test DXF file with MTEXT entities containing various formatting codes.

This creates test fixtures for validating MTEXT formatting code stripping.
The file includes MTEXT entities with:
- Paragraph alignment codes (\\pxqc;, \\pxql;, \\pxqr;, \\pxqj;)
- Paragraph breaks (\\P)
- Underline/overline (\\L, \\l, \\O, \\o)
- Color codes (\\C...;)
- Font changes (\\f...;)
- Text height (\\H...;)
- Tab characters (\\~)
- Complex combinations

Expected outputs after formatting cleanup are documented below.
"""

import ezdxf


# Create new DXF document
doc = ezdxf.new("R2010")
msp = doc.modelspace()

# Create layers
doc.layers.add("FORMATTING_TEST", color=7)  # White

# Scenario 1: Paragraph alignment codes
# \\pxqc; = center alignment, should be stripped
mtext1 = msp.add_mtext(
    "\\pxqc;CENTERED TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 0),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "CENTERED TEXT"

# Scenario 2: Paragraph breaks
# \\P = paragraph break, should become space
mtext2 = msp.add_mtext(
    "LINE ONE\\PLINE TWO",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 10),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "LINE ONE LINE TWO"

# Scenario 3: Complex example from bug report
# \\pxqc;MENS CASUAL\\P PANTS should become "MENS CASUAL PANTS"
mtext3 = msp.add_mtext(
    "\\pxqc;MENS CASUAL\\P PANTS",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 20),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "MENS CASUAL PANTS"

# Scenario 4: Underline codes
# \\L = start underline, \\l = stop underline
mtext4 = msp.add_mtext(
    "NORMAL \\LUNDERLINED\\l TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 30),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "NORMAL UNDERLINED TEXT"

# Scenario 5: Overline codes
# \\O = start overline, \\o = stop overline
mtext5 = msp.add_mtext(
    "NORMAL \\OOVERLINED\\o TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 40),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "NORMAL OVERLINED TEXT"

# Scenario 6: Color codes
# \\C1; = color 1 (red in ACI)
mtext6 = msp.add_mtext(
    "NORMAL \\C1;RED\\C7; WHITE",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 50),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "NORMAL RED WHITE"

# Scenario 7: Font changes
# \\fArial|b1|i0; = Arial Bold
mtext7 = msp.add_mtext(
    "NORMAL \\fArial|b1|i0;BOLD\\fArial|b0|i0; TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 60),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "NORMAL BOLD TEXT"

# Scenario 8: Text height changes
# \\H2.5; = height 2.5
mtext8 = msp.add_mtext(
    "NORMAL \\H5;BIG\\H2.5; TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 70),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "NORMAL BIG TEXT"

# Scenario 9: Multiple paragraph breaks (should collapse spaces)
mtext9 = msp.add_mtext(
    "WORD1\\P\\PWORD2",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 80),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "WORD1 WORD2" (multiple breaks become single space)

# Scenario 10: Plain text without formatting (should be preserved as-is)
mtext10 = msp.add_mtext(
    "PLAIN TEXT WITHOUT FORMATTING",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 90),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "PLAIN TEXT WITHOUT FORMATTING"

# Scenario 11: Left alignment
mtext11 = msp.add_mtext(
    "\\pxql;LEFT ALIGNED",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 100),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "LEFT ALIGNED"

# Scenario 12: Right alignment
mtext12 = msp.add_mtext(
    "\\pxqr;RIGHT ALIGNED",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 110),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "RIGHT ALIGNED"

# Scenario 13: Justified
mtext13 = msp.add_mtext(
    "\\pxqj;JUSTIFIED TEXT",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 120),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "JUSTIFIED TEXT"

# Scenario 14: Complex mixed formatting
mtext14 = msp.add_mtext(
    "\\pxqc;\\LHEADER\\l\\PNORMAL \\C1;RED\\C7; TEXT\\P\\H5;LARGE\\H2.5; END",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 130),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "HEADER NORMAL RED TEXT LARGE END"

# Scenario 15: Tab character (non-breaking space)
# \\~ = non-breaking space in MTEXT
mtext15 = msp.add_mtext(
    "WORD1\\~WORD2",
    dxfattribs={
        "layer": "FORMATTING_TEST",
        "insert": (0, 140),
        "char_height": 2.5,
        "color": 7,
    },
)
# Expected: "WORD1 WORD2" (non-breaking space becomes regular space)

# Save DXF file
doc.saveas("app/tests/assets/mtext_formatting_test.dxf")
print("Created app/tests/assets/mtext_formatting_test.dxf with MTEXT formatting scenarios")
print("\nExpected cleaned text for each MTEXT entity:")
print("1. '\\pxqc;CENTERED TEXT' -> 'CENTERED TEXT'")
print("2. 'LINE ONE\\PLINE TWO' -> 'LINE ONE LINE TWO'")
print("3. '\\pxqc;MENS CASUAL\\P PANTS' -> 'MENS CASUAL PANTS'")
print("4. 'NORMAL \\LUNDERLINED\\l TEXT' -> 'NORMAL UNDERLINED TEXT'")
print("5. 'NORMAL \\OOVERLINED\\o TEXT' -> 'NORMAL OVERLINED TEXT'")
print("6. 'NORMAL \\C1;RED\\C7; WHITE' -> 'NORMAL RED WHITE'")
print("7. 'NORMAL \\fArial|b1|i0;BOLD\\fArial|b0|i0; TEXT' -> 'NORMAL BOLD TEXT'")
print("8. 'NORMAL \\H5;BIG\\H2.5; TEXT' -> 'NORMAL BIG TEXT'")
print("9. 'WORD1\\P\\PWORD2' -> 'WORD1 WORD2'")
print("10. 'PLAIN TEXT WITHOUT FORMATTING' -> 'PLAIN TEXT WITHOUT FORMATTING'")
print("11. '\\pxql;LEFT ALIGNED' -> 'LEFT ALIGNED'")
print("12. '\\pxqr;RIGHT ALIGNED' -> 'RIGHT ALIGNED'")
print("13. '\\pxqj;JUSTIFIED TEXT' -> 'JUSTIFIED TEXT'")
print("14. Complex mixed -> 'HEADER NORMAL RED TEXT LARGE END'")
print("15. 'WORD1\\~WORD2' -> 'WORD1 WORD2'")
