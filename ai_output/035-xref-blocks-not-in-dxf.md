# XREF Blocks Not Present in DXF File

## Executive Summary

The block `95103BGM$0$DOT` visible in AutoCAD is an **XREF (external reference) block** that is NOT embedded in the DXF file. The naming pattern `XREFNAME$0$BLOCKNAME` indicates this block comes from an attached external reference file named `95103BGM`. When a DXF is saved without binding XREFs, these blocks are NOT included in the file - they're loaded dynamically by AutoCAD from the external reference file.

## Table Summary

| Evidence | Finding |
|----------|---------|
| Block `95103BGM$0$DOT` in file | NOT FOUND |
| String "95103BGM" in raw DXF | NOT FOUND |
| String "95103" in raw DXF | NOT FOUND |
| Coordinates (650.710328, 419.074664) in file | NOT FOUND |
| INSERT entities in file | 1,269 found (none match) |
| Entities near target position | LINE entities only, no INSERT |
| XREF references in BLOCK_RECORD | NONE (no XREF flags set) |
| Blocks with `$0$` pattern | NONE |

## Relevant Files

- `app/tests/assets/samples/437 Greenwich - EFP- 4-18-2022.dxf` - The 2.0 MB DXF file (234,512 lines)
- `app/core/extractor.py` - Extractor uses `doc.blocks` and modelspace `INSERT` entities

## How XREF Block Names Work

The pattern `95103BGM$0$DOT` follows AutoCAD's XREF naming convention:

```
XREFNAME$0$BLOCKNAME
   │      │    │
   │      │    └── Block name WITHIN the XREF ("DOT")
   │      └── Separator (always $0$)
   └── Name of the external reference file ("95103BGM")
```

When you attach an XREF named `95103BGM.dwg`, all blocks in that file become accessible with this prefix. However, these blocks are **NOT stored in your DXF file** - they exist only in the external reference.

## Why the Blocks Are Visible in AutoCAD But Not in the DXF

| Scenario | AutoCAD Behavior | DXF File Contents |
|----------|-----------------|-------------------|
| XREF Attached | Blocks visible, selectable | XREF path stored, blocks NOT embedded |
| XREF Bound | Blocks visible, selectable | Blocks renamed to `XREFNAME$0$BLOCK` and embedded |
| XREF Detached | Blocks disappear | No XREF data at all |
| DXF Export | Only embedded content exported | XREF blocks excluded unless bound |

**Current state:** The DXF file has NO XREF references and NO blocks with the `$0$` pattern. This means either:
1. XREFs were detached before saving
2. The DXF was exported without binding XREFs
3. You're viewing a different file in AutoCAD (perhaps a DWG with live XREF attachments)

## File Evidence

```
File: 437 Greenwich - EFP- 4-18-2022.dxf
Size: 2,068,864 bytes (2.0 MB)
Lines: 234,512
Modified: 2025-12-10 19:30:06
INSERT entities: 1,269
Blocks with $ in name: 9 (all A$C pattern - dynamic blocks, NOT XREFs)
```

The 9 blocks with `$` are `A$C*` pattern (anonymous dynamic blocks), NOT `$0$` pattern (XREF blocks).

## Coordinate Search Results

The user-provided coordinates `(650.710328, 419.074664)` were searched:
- **No INSERT entity exists at these coordinates**
- Nearby entities are LINE entities on layers: `EX-Int Walls`, `EX-Fixture`, `EX-Columns`
- Nearest INSERT entities are at ~(655, 454) and ~(680, 395) - different blocks (`ENGO-W24-84`)

## Recommendations

1. **Verify file identity** - Compare the file in AutoCAD with the repo file:
   - In AutoCAD: `DWGPROPS` command shows file path
   - Check if you're viewing a DWG (may have XREFs) vs the DXF (XREFs stripped)

2. **Bind XREFs before export** - If you need XREF blocks in the DXF:
   - In AutoCAD: `XREF` command → select XREF → Bind
   - This converts XREF blocks to local blocks with `XREFNAME$0$BLOCKNAME` naming

3. **Export correctly** - When saving DXF for extraction:
   - Use `SAVEAS` to DXF format
   - Consider `WBLOCK` to export only model space with bound XREFs

## Next Steps

1. Open the exact file path `app/tests/assets/samples/437 Greenwich - EFP- 4-18-2022.dxf` in AutoCAD
2. Verify the block `95103BGM$0$DOT` is NOT present (it won't be)
3. If the blocks are needed, re-export the original DWG with XREFs bound
