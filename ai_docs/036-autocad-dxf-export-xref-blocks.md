# AutoCAD 2024: Exporting DWG to DXF with Embedded XREF Blocks

## Executive Summary

The DWG file contains blocks with XREF naming patterns (`95103BGM$0$DOT`) that were previously bound and are now local to the file. However, these blocks are not appearing in the DXF export. This guide provides step-by-step AutoCAD 2024 instructions to export a DWG to DXF while preserving all block definitions, including formerly-bound XREF blocks.

## Table Summary

| Method | Reliability | Preserves All Blocks | Complexity |
|--------|-------------|---------------------|------------|
| WBLOCK (Entire Drawing) | Highest | Yes | Low |
| EXPORTTOAUTOCAD | High | Yes | Low |
| SAVEAS DXF | Medium | Usually | Low |
| ETRANSMIT + Convert | Highest | Yes (flattens XREFs) | Medium |

## Relevant Files

- `437 Greenwich - EFP- 4-18-2022.dwg` - Source DWG containing the `95103BGM$0$DOT` block
- `app/tests/assets/samples/437 Greenwich - EFP- 4-18-2022.dxf` - Current DXF export missing blocks
- `ai_output/035-xref-blocks-not-in-dxf.md` - Previous investigation confirming blocks missing from DXF

## Pre-Export Verification (Required)

Before exporting, verify the blocks exist and are exportable:

### Step 1: Verify Block Exists in DWG
```
Command: BEDIT
```
1. Type `BEDIT` and press Enter
2. In the "Edit Block Definition" dialog, scroll to find `95103BGM$0$DOT`
3. If found, the block IS in the file - proceed to export
4. Press Escape to cancel

### Step 2: Check Layer Status
```
Command: LAYER
```
1. Type `LAYER` and press Enter
2. Click "Thaw All Layers" icon (sun with snowflake)
3. Click "Turn All Layers On" icon (lightbulb)
4. Click "Unlock All Layers" icon
5. Close the Layer Properties Manager

### Step 3: Verify Block Insertions Exist
```
Command: QSELECT
```
1. Type `QSELECT` and press Enter
2. Set "Apply to": Entire drawing
3. Set "Object type": Block Reference
4. Set "Properties": Name
5. Set "Operator": = Equals
6. Set "Value": `95103BGM$0$DOT`
7. Click OK - this will select all instances of the block

## Method 1: WBLOCK Export (Recommended)

This is the most reliable method for preserving all blocks.

### Steps
```
Command: WBLOCK
```

1. Type `WBLOCK` and press Enter
2. In the "Write Block" dialog:
   - **Source section**: Select "Entire drawing" radio button
   - **Destination section**:
     - Click the browse button (...)
     - Navigate to your desired folder
     - Change "Save as type" to `AutoCAD 2018 DXF (*.dxf)` or `AutoCAD 2013 DXF (*.dxf)`
     - Enter filename: `437 Greenwich - EFP- 4-18-2022.dxf`
3. Click OK

### Why This Works
WBLOCK creates a new file with ALL block definitions from the source drawing, regardless of whether they're inserted or just defined.

## Method 2: EXPORTTOAUTOCAD Command

This command creates a "flattened" version with all XREFs and blocks embedded.

### Steps
```
Command: EXPORTTOAUTOCAD
```

1. Type `EXPORTTOAUTOCAD` and press Enter
2. In the "Export to AutoCAD" dialog:
   - **File Format**: Select `AutoCAD 2018 DXF` or `AutoCAD 2013 DXF`
   - **Bind Xrefs**: Check this box (even if already bound)
   - **Bind type**: Select "Insert" for cleanest results
3. Click OK
4. Choose save location and filename

## Method 3: ETRANSMIT + Convert (Most Thorough)

If other methods fail, ETRANSMIT guarantees all dependencies are included.

### Steps
```
Command: ETRANSMIT
```

1. Type `ETRANSMIT` and press Enter
2. Click "Transmittal Setups..." button
3. Click "New..." and name it "DXF Export"
4. Configure:
   - **Transmittal package type**: Folder (set of files)
   - **File format**: AutoCAD 2018 Drawing Format
   - **Bind external references**: Check this box
   - **Include fonts**: Uncheck (not needed for DXF)
5. Click OK, then "Transmittal Setup" dialog OK
6. Click "OK" to create the transmittal
7. Open the resulting DWG file
8. Use SAVEAS to save as DXF:
   ```
   Command: SAVEAS
   ```
   - Select DXF format
   - Save the file

## Method 4: SAVEAS with DXF Options

Standard export, but verify options are correct.

### Steps
```
Command: SAVEAS
```

1. Type `SAVEAS` and press Enter
2. In "Save Drawing As" dialog:
   - **Files of type**: Select `AutoCAD 2018 DXF (*.dxf)` or lower
   - **File name**: Enter desired name
3. **IMPORTANT**: Click "Tools" dropdown (top-right of dialog)
4. Click "Options..."
5. In "Saveas Options" dialog, DXF Options tab:
   - **Format**: ASCII (not Binary) - more compatible
   - **Select objects**: UNCHECK - exports entire drawing
   - **Save proxy images of custom objects**: Check
6. Click OK, then Save

## Post-Export Verification

After exporting, verify the DXF contains the blocks:

### Option A: Open in AutoCAD
1. Open the new DXF file in AutoCAD
2. Run `BEDIT` and look for `95103BGM$0$DOT`
3. Run `INSERT` command and check the block list

### Option B: Text Search
1. Open the DXF file in a text editor (Notepad++, VS Code)
2. Search for `95103BGM$0$DOT`
3. Should appear in the BLOCKS section

### Option C: Use the Extractor
```bash
uv run python app/main.py
```
- Open the new DXF file
- The block should appear in the extraction results

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Block defined but not exported | Block has 0 insertions - use WBLOCK which exports definitions |
| Block on locked/frozen layer | Unlock and thaw all layers before export |
| Block is proxy object | Install original application or use EXPORTTOAUTOCAD |
| DXF file too large | Use Binary DXF format or AutoCAD 2013 version |
| Block still missing | Block may be nested inside another block - export parent block |

## If All Methods Fail: Manual Block Extraction

If the block is nested inside another block:

```
Command: BEDIT
```
1. Edit the parent block that contains the XREF blocks
2. Select the nested block insertion
3. Type `EXPLODE` to convert to individual entities
4. Exit block editor and save changes
5. Re-export using WBLOCK method

## Recommended Export Settings Summary

| Setting | Value |
|---------|-------|
| DXF Version | AutoCAD 2018 DXF or AutoCAD 2013 DXF |
| Format | ASCII (not Binary) |
| Bind XREFs | Yes |
| Include all layers | Yes (thaw/turn on all) |
| Select objects | No (export entire drawing) |
| Method | WBLOCK with "Entire drawing" |

## Next Steps

1. Open `437 Greenwich - EFP- 4-18-2022.dwg` in AutoCAD 2024
2. Run the pre-export verification steps
3. Use Method 1 (WBLOCK) to export to DXF
4. Verify the export contains `95103BGM$0$DOT` block
5. Replace the existing DXF in `app/tests/assets/samples/`
