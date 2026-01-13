# End Cap Parameter and AutoCAD Visibility Connection

## Executive Summary

The "End Cap" dropdown you see in the Properties palette **IS** the visibility parameter - it's just been given a custom name by the block creator. In AutoCAD dynamic blocks, visibility parameters can be named anything. The dropdown options (Left End Cap, Right End Cap, etc.) are the visibility states within that parameter. The current INSERT has "Right End Cap" selected, which is why you see the extra 1.5-unit geometry.

## Table Summary

| Concept | AutoCAD Term | What You See | DXF Storage |
|---------|--------------|--------------|-------------|
| Parameter Name | Visibility Parameter | "End Cap" dropdown label | Group code 300: `End Cap` |
| Current Value | Visibility State | "Right End Cap" selected | XRECORD group code 1: `Right End Cap` |
| Available Options | Visibility States | Dropdown list | Group code 303 entries |
| Controlled Geometry | Visibility Entities | End cap polylines | Handle lists per state |

## Relevant Files

- **app/tests/assets/samples/sample-blocks.dxf:64972-65142** - BLOCKVISIBILITYPARAMETER definition showing "End Cap" parameter and states
- **app/tests/assets/samples/sample-blocks.dxf:66750** - XRECORD storing current state "Right End Cap" for the INSERT
- **ai_output/080-dynamic-block-end-cap-visibility-analysis.md** - Previous analysis (incorrectly suggested looking for generic "Visibility" label)

## How Visibility Parameters Work in AutoCAD

### 1. Parameter Naming

When creating a dynamic block, the block author:
1. Adds a **Visibility Parameter** from Block Authoring Palettes
2. **Names the parameter** anything they want (e.g., "End Cap", "Configuration", "Style")
3. Creates **visibility states** within that parameter

The parameter name becomes the **property label** you see in the Properties palette.

### 2. Your Block's Structure

```
BLOCKVISIBILITYPARAMETER (Handle E58)
├── Parameter Name: "End Cap"          ← What you see as the dropdown label
├── Base Point: (72.25, -51.0)
└── Visibility States:
    ├── "No End Cap"     → Shows 6 entities (main body only)
    ├── "Left End Cap"   → Shows 7 entities (adds handle E68)
    ├── "Right End Cap"  → Shows 7 entities (adds handle E69)
    └── "Both End Cap"   → Shows 8 entities (adds E68 + E69)
```

### 3. Entity Handle Mapping

| Entity Handle | Description | Visible In |
|---------------|-------------|------------|
| E63-E67, E6A | Main body geometry | All states |
| E68 | Left end cap (1.5 wide) | Left End Cap, Both End Cap |
| E69 | Right end cap (1.5 wide) | Right End Cap, Both End Cap |

## DXF Evidence

### Parameter Definition (lines 64972-65142)

```dxf
BLOCKVISIBILITYPARAMETER
  5
E58                          ← Handle
...
300
End Cap                      ← Parameter name (Properties label)
...
303
No End Cap                   ← State 1
 94
        6                    ← 6 entities visible
...
303
Right End Cap                ← State 3
 94
        7                    ← 7 entities visible (adds E69)
332
E69                          ← Right end cap handle
```

### Current INSERT State (line 66750)

```dxf
XRECORD
  5
F16
...
  1
Right End Cap                ← Current visibility state value
```

## Why Previous Report Was Slightly Off

The previous report (080) suggested looking for a generic "Visibility" property in the Properties palette. This was incorrect because:

1. Visibility parameters can have **any name** - the block creator chose "End Cap"
2. The "End Cap" dropdown you found **IS** the visibility control
3. There is no separate "Visibility" label - the parameter name replaces it

## How to Read the Properties Palette

| Section | Property | Meaning |
|---------|----------|---------|
| Custom | **End Cap** | This IS the visibility parameter |
| | Dropdown options | These ARE the visibility states |
| | Current selection | The active visibility state for this INSERT |

## Verification Steps in AutoCAD

1. **Properties Palette**: The "End Cap" dropdown IS the visibility control - changing it changes which geometry is visible

2. **Block Editor**:
   - Double-click block to enter Block Editor
   - Select the visibility grip (triangle icon at 72.25, -51)
   - Properties will show "End Cap" as the parameter name
   - Visibility States panel shows all 4 states

3. **Test by changing**: Select the INSERT, change "End Cap" dropdown from "Right End Cap" to "No End Cap" - the 1.5-unit extra geometry should disappear

## Simple List Summary

- The "End Cap" dropdown in Properties IS the visibility parameter - block creators name visibility parameters themselves
- Dropdown options (No End Cap, Left, Right, Both) are the visibility states that control which geometry shows
- Your INSERT currently has "Right End Cap" selected, making the right 1.5-unit flap visible
- Changing the dropdown selection will show/hide the end cap geometry in real-time
- There is no separate "Visibility" property - the custom parameter name replaces it
- This is stored in DXF as BLOCKVISIBILITYPARAMETER with XRECORD tracking the current state
