# Dynamic Block End Cap Visibility Analysis

## Executive Summary

The 1.5-unit "extra area" you observe in normal view but not in Block Editor is caused by **dynamic block visibility states**. The block `DD5X-12ULEP` has 4 visibility states controlling "End Cap" geometry on both sides. When placed as an INSERT (`*U22`), the visibility state determines which end caps are shown. The Block Editor displays the block in its default/edit state, which may have different visibility.

## Table Summary

| Aspect | Value | Notes |
|--------|-------|-------|
| Block Name | DD5X-12ULEP | Original block definition |
| Anonymous Reference | *U22 | Created when dynamic parameters applied |
| Total Width (both caps) | 147.5 | From x=-1.5 to x=146.0 |
| Main Body Width | 144.5 | From x=0 to x=144.5 |
| Left End Cap Width | 1.5 | From x=-1.5 to x=0 |
| Right End Cap Width | 1.5 | From x=144.5 to x=146.0 |
| Visibility States | 4 | No End Cap, Left, Right, Both |
| Content Zone Width | 144.5 | Excludes end caps (filtered out) |
| Suggested Trim Left | 1.5 | Offset from end cap to main body |
| Suggested Trim Right | 1.5 | Offset from end cap to main body |

## Relevant Files

- **app/tests/assets/samples/sample-blocks.dxf** - The DXF file containing the block
- **ai_output/079-unit-setting-impact-analysis.md** - Previous analysis showing 1.5 trim values
- **ai_output/078-block-trimming-calculation-analysis.md** - Detailed trim calculation breakdown
- **app/core/geometry.py:1634-1909** - `_detect_content_zone()` - Filters out end caps as small polygons

## What Are Dynamic Block Visibility States?

Dynamic blocks in AutoCAD can have **visibility parameters** that show/hide geometry based on a named state. This allows a single block definition to have multiple visual configurations.

```
DD5X-12ULEP (Dynamic Block)
├── Base Geometry (always visible)
│   └── Main body: x=0 to x=144.5
├── Visibility State: "No End Cap"
│   └── Shows only main body
├── Visibility State: "Left End Cap"
│   └── Shows main body + left flap (x=-1.5 to x=0)
├── Visibility State: "Right End Cap"
│   └── Shows main body + right flap (x=144.5 to x=146.0)
└── Visibility State: "Both End Cap"
    └── Shows main body + both flaps (total width 147.5)
```

## Why Normal View and Block Editor Differ

| View | What You See | Reason |
|------|--------------|--------|
| **Normal View** (INSERT reference) | Extra 1.5 on right side | The INSERT has a visibility state set (likely "Right End Cap" or "Both End Cap") |
| **Block Editor** | No extra section | Block Editor shows the block in a default/edit state, typically "No End Cap" or the first visibility state |

### Technical Explanation

1. **Anonymous Block Creation**: When you place a dynamic block and change its parameters, AutoCAD creates an anonymous copy (e.g., `*U22`) with the modified geometry/state "baked in"

2. **Geometry Exists in Both**: All end cap geometry exists in both `*U22` and `DD5X-12ULEP` - they have identical 59 entities with the same coordinates

3. **Visibility State Application**: The difference is which entities are marked as "visible" for the current state. In normal view, the INSERT's extension dictionary stores the active visibility state

4. **Block Editor Default**: When you open Block Editor, AutoCAD shows a default visibility state (often the first defined state or "No End Cap")

## End Cap Geometry Details

The end caps are separate LWPOLYLINE entities on Layer 0:

```
Left End Cap:
  Handle: E68 (DD5X) / EA8 (*U22)
  Vertices: (0,-3) → (-1.5,-3) → (-1.5,-45) → (0,-45)
  Width: 1.5 units

Right End Cap:
  Handle: E69 (DD5X) / EA9 (*U22)
  Vertices: (146,-3) → (144.5,-3) → (144.5,-45) → (146,-45)
  Width: 1.5 units
```

## Why Content Zone Detection Filters Out End Caps

The extractor's content zone detection calculates trim values of 1.5 on each side because:

1. **Paint bucket algorithm** finds all closed polygons including end caps
2. **Min side filter** (0.394 inches) filters out narrow 4-sided rectangles
3. **End caps** (1.5 wide x 42 tall) pass the side filter but their **net area** after subtracting overlapping polygons may be filtered
4. **Surviving polygons** form the "content zone" at x=0 to x=144.5
5. **Trim values** = block bbox (147.5) minus content zone bbox (144.5) = 3.0 total (1.5 per side)

## How to Verify in AutoCAD

1. **Check Current Visibility State**:
   - Select the block INSERT
   - Open Properties palette
   - Look for "Visibility" parameter showing current state name

2. **View All States in Block Editor**:
   - Double-click block to enter Block Editor
   - Look for "Visibility States" panel
   - Click through each state to see what geometry appears

3. **Check Available States**:
   - In Block Editor, Block Authoring Palettes → Parameters
   - Select the visibility parameter
   - See list of defined states: No End Cap, Left End Cap, Right End Cap, Both End Cap

## Simple List Summary

- Block has 4 visibility states: "No End Cap", "Left End Cap", "Right End Cap", "Both End Cap"
- End caps are 1.5-unit wide rectangular polylines on each side of the main body
- INSERT reference (*U22) has a visibility state showing the right (or both) end caps
- Block Editor displays a default state where end caps may be hidden
- All geometry exists in both definitions - only visibility assignment differs
- Content zone detection correctly excludes end caps, suggesting 1.5 trim values
- This is expected AutoCAD dynamic block behavior, not a bug
