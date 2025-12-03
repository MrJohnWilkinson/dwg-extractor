# Bug: Missing Block Detection Investigation

## Bug Description
User reports that when extracting from `app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf`, the extractor finds the block `Grocery_Gondola_Combined - 2000H  - 1350W _505_695_-82007408-GROUND FFL` but is NOT detecting a similar block `Grocery_Gondola_Combined - 2000H  - 1350W _695_505_-82006595-GROUND FFL`.

**Expected:** Both blocks should be extracted if they exist in the file.
**Actual:** Only one block is extracted.

## Problem Statement
Determine whether the extractor is missing blocks that exist in the DXF file, or whether the reported "missing" block simply does not exist in the file.

## Solution Statement
After thorough investigation, **this is NOT a bug in the extractor**. The block `Grocery_Gondola_Combined - 2000H  - 1350W _695_505_-82006595-GROUND FFL` does not exist in the DXF file. The investigation confirmed:

1. The block definition does not exist in `doc.blocks`
2. No INSERT entity references this block in modelspace
3. No nested INSERT references this block inside other blocks
4. The raw text strings `695_505` and `82006595` do not exist anywhere in the DXF file

The only similar block that exists is `Grocery_Gondola_Combined - 2000H  - 1350W _505_695_-82007408-GROUND FFL` (note the different pattern: `_505_695_` vs `_695_505_` and different ID: `-82007408` vs `-82006595`).

## Steps to Reproduce
1. Load the DXF file: `app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf`
2. Search for block definitions containing `695_505` - none found
3. Search for INSERT entities containing `695_505` - none found
4. Search for the ID `82006595` in any form - not found
5. The extractor correctly outputs all 16 Grocery_Gondola blocks that exist in the file

## Root Cause Analysis
The reported "missing" block does not exist in the provided DXF file. Possible explanations:
1. The user may be looking at a different DXF file that contains this block
2. The block may have been removed or renamed in the current version of the file
3. There may be confusion between similar block names (`_505_695_` vs `_695_505_`)

## Relevant Files
- `app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf` - The DXF file being analyzed
- `app/core/extractor.py` - The extraction logic (verified working correctly)

## Step by Step Tasks

### 1. Verify Investigation Results
- Run the verification script to confirm the block does not exist
- Document all Grocery_Gondola blocks that DO exist in the file for reference

```python
import ezdxf

doc = ezdxf.readfile('app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf')

# Check block definitions
for block_def in doc.blocks:
    if 'Grocery_Gondola' in block_def.name:
        print(f'Block: {block_def.name}')

# Verify missing block does not exist
print('695_505 found:', any('695_505' in b.name for b in doc.blocks))
print('82006595 found:', any('82006595' in b.name for b in doc.blocks))
```

### 2. Clarify with User
- Ask the user to verify they are using the correct DXF file
- Ask if the block exists in a different file or version
- Request the specific source where they saw this block name

### 3. Close Issue as "Not a Bug"
- No code changes required
- The extractor is working correctly
- Document findings for future reference

## Validation Commands
Execute every command to validate the investigation is correct.

- `uv run pytest app/tests/` - Run all tests to ensure extractor is working correctly
- `uv run python -c "import ezdxf; doc=ezdxf.readfile('app/tests/assets/samples/2025-09-30 - 2030_BP ARCH (R25) - Floor Plan - GROUND FFL.dxf'); print('695_505 exists:', any('695_505' in b.name for b in doc.blocks))"` - Verify the block pattern does not exist

## Notes
- The extractor found 1111 unique blocks and 2073 total insertions in this file
- There are 14 Grocery_Gondola_Combined blocks with various dimensions
- The only block with 1350W width is `Grocery_Gondola_Combined - 2000H  - 1350W _505_695_-82007408-GROUND FFL`
- All other Grocery_Gondola blocks have 1240W width
- This appears to be a case of user confusion about which file contains which blocks, not an extractor bug
