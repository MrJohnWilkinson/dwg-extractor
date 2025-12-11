# Missing Blocks Investigation: 95103BGM$0$PANEL and 95103BGM$0$DOT

## Executive Summary

Investigation into why blocks `95103BGM$0$PANEL` and `95103BGM$0$DOT` do not appear in the extraction output for `437 Greenwich - EFP- 4-18-2022.dxf`. **Finding: These block names do not exist in the DXF file.** This is not an extractor bug - the blocks are simply not present in the specified file.

## Table Summary

| Investigation Step | Result | Conclusion |
|-------------------|--------|------------|
| Search `doc.blocks` for exact name | Not found | Block definitions don't exist |
| Search `doc.blocks` for partial match (95103, BGM, PANEL, DOT) | 0 matches | No similar block names |
| Search modelspace INSERT entities | Not found | No insertions reference these blocks |
| Raw file grep for "95103BGM" | Empty | String not in DXF file at all |
| Raw file grep for "BGM" | Empty | String not in file |
| Search all DXF files in workspace | Not found | String doesn't exist in any DXF |
| Nested block name search | Not found | Not a nested block reference |
| A$C block XDATA resolution | No match | No A$C blocks resolve to these names |

## Relevant Files

- `app/tests/assets/samples/437 Greenwich - EFP- 4-18-2022.dxf` - The DXF file under investigation (2.0 MB)
- `app/core/extractor.py` - The extraction logic that was traced through
- `app/core/types.py` - Type definitions for extraction results
- `app/core/constants.py` - Constants including supported extensions

## Extractor Flow Analysis

The extractor processes blocks in this sequence:

### Step 1: Load DXF File
```python
doc = ezdxf.readfile(file_path)  # Line 1087
```
File loads successfully with ezdxf.

### Step 2: Analyze Block Definitions (Lines 1166-1299)
For each block in `doc.blocks`:
1. Skip system blocks (`*Model_Space`, `*Paper_Space`)
2. For `*U` anonymous blocks: Try to resolve via XDATA `AcDbBlockRepBTag`
3. For `A$C` anonymous blocks: Try to resolve via XDATA, use raw name if unresolved
4. Skip other `*` prefixed blocks (dimension, hatch patterns)
5. Extract entity counts and geometry analysis

**Finding at this step:** No block definition contains "95103BGM" in its name.

### Step 3: Scan Modelspace INSERT Entities (Lines 1304-1515)
For each entity in modelspace:
1. If entity is an INSERT, get `entity.dxf.name`
2. Resolve anonymous block names using the mapping built in Step 2
3. Count block insertions and track layer associations

**Finding at this step:** No INSERT entity references a block containing "95103BGM".

### Step 4: Build Output (Lines 1665-1686)
Compile all extraction data into `ExtractionResult`.

**Result:** 52 unique blocks extracted, none named `95103BGM$0$PANEL` or `95103BGM$0$DOT`.

## Blocks Actually Found in File

The file contains 58 total block definitions with 52 having modelspace insertions:

| Block Name | Insertion Count |
|------------|-----------------|
| _ArchTick | 408 |
| ENGO-2424-84 | 339 |
| ENGO-W30-84 | 93 |
| ENGO-W24-84 | 70 |
| ENGO-2222-84 | 53 |
| ENGO-1818-84 | 27 |
| ENGO-2428-84 | 26 |
| BOF -3ft Deep  Wakefern Milk Mover | 23 |
| RLN-5DR | 23 |
| ENGO-2424-E-84 | 22 |
| A$C86afe4d1 | 18 |
| ... (42 more blocks) | ... |

The file also has 9 unresolved A$C anonymous blocks that could not be resolved to original names (all reported in Extraction Issues sheet).

## Raw File Search Evidence

```bash
$ grep -i "95103BGM" "437 Greenwich - EFP- 4-18-2022.dxf"
# (no output)

$ grep -i "95103" "437 Greenwich - EFP- 4-18-2022.dxf"
# (no output)

$ grep -i "BGM" "437 Greenwich - EFP- 4-18-2022.dxf"
# (no output)
```

The strings do not exist anywhere in the raw DXF file content.

## Recommendations

1. **Verify the correct file** - The blocks may exist in a different DXF file
2. **Check file version** - If the file was recently modified, the blocks may have been removed
3. **Check source documentation** - Verify where the block names `95103BGM$0$PANEL` and `95103BGM$0$DOT` were originally referenced

## Next Steps

1. Obtain the correct DXF file containing these blocks (if one exists)
2. Alternatively, confirm the correct block names to search for in this file
3. If blocks should exist but don't, investigate the DXF file's creation/export process
