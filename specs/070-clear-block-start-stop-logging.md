# Chore: Add Clear Block Start/Stop Logging

## Chore Description
Currently, block processing boundaries in the debug logs are confusing because:
1. The "start" marker (`[BlockName] Detecting content zone...`) is actually in geometry.py and only marks when content zone detection begins - NOT when actual block processing starts
2. The bounding box calculation (`Bounding box: processing entity type...`) happens BEFORE the "Detecting content zone" message
3. The end marker (`[TIMING] Block 'BlockName' completed in X.Xs`) only appears for blocks taking >1 second, making it impossible to see where fast blocks end

This makes it difficult to:
- Parse logs programmatically to extract per-block timing
- Visually identify where one block's processing ends and another begins
- Debug performance issues for fast blocks

The solution is to add explicit, unconditional START and END markers in extractor.py at the actual boundaries of block processing.

## Relevant Files
Use these files to resolve the chore:

- **app/core/extractor.py** (lines 1207-1303) - Contains the main block processing loop (PHASE 2). This is where we need to add the START marker (after `effective_name` is determined, around line 1232) and make the END marker unconditional (lines 1297-1302).
- **app/core/geometry.py** (line 1142) - Contains the existing `[BlockName] Detecting content zone...` INFO message. No changes needed - this message provides useful phase information within the START/END boundaries.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Add Block Processing START Marker
In `app/core/extractor.py`, add an INFO log immediately after `effective_name` is determined (after line 1230, before line 1232):

- Add: `logger.info(f"[BLOCK START] '{effective_name}'")`
- This provides a clear, consistent start marker that appears BEFORE any geometry calculations
- The format `[BLOCK START]` is distinct and easily grep-able

### Step 2: Make Block Processing END Marker Unconditional
In `app/core/extractor.py`, modify the timing log (lines 1297-1302):

- Remove the `if block_duration > 1.0:` condition
- Change the log message from `[TIMING] Block '{effective_name}' completed in {block_duration:.1f}s` to `[BLOCK END] '{effective_name}' ({block_duration:.3f}s)`
- Use 3 decimal places (milliseconds) for better precision on fast blocks
- The format `[BLOCK END]` pairs with `[BLOCK START]` for easy parsing

### Step 3: Update the Block Processing Log Boundary Guide
Update `ai_output/073-block-processing-log-boundary-guide.md` to reflect the new log patterns:

- Update the Table Summary with the new START/END markers
- Update examples to show the new format
- Remove notes about conditional timing logs

### Step 4: Run Validation Commands
Execute the validation commands to ensure zero regressions.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/core/test_logger.py -v` - Run logger tests
- `uv run pytest app/tests/core/extractor/ -v` - Run extractor tests to ensure no regressions
- `uv run mypy app/core/extractor.py` - Type check the modified file
- `uv run ruff check app/core/extractor.py` - Lint check the modified file

## Notes

### Expected Log Output After Changes
```
14:06:55.147 [INFO] [BLOCK START] 'FreshProduce_ScoopWeighPottles_Wood - Type 1-38979240-GROUND FFL'
14:06:55.147 [DEBUG] Bounding box: processing entity type LINE
... (bounding box DEBUG messages) ...
14:06:55.193 [INFO] [FreshProduce_ScoopWeighPottles_Wood - Type 1-38979240-GROUND FFL] Detecting content zone...
... (content zone DEBUG messages) ...
14:08:12.487 [INFO] [FreshProduce_ScoopWeighPottles_Wood - Type 1-38979240-GROUND FFL] Content zone detected: 476.00 x 357.57
14:08:12.489 [INFO] [BLOCK END] 'FreshProduce_ScoopWeighPottles_Wood - Type 1-38979240-GROUND FFL' (77.342s)
```

### Grep Commands for Parsing
After this change, users can easily extract block timing with:
```bash
grep "\[BLOCK" output.log
```
Output:
```
[BLOCK START] 'BlockA'
[BLOCK END] 'BlockA' (0.002s)
[BLOCK START] 'BlockB'
[BLOCK END] 'BlockB' (77.342s)
```

### Why Keep the geometry.py "Detecting content zone" Message
The existing `[BlockName] Detecting content zone...` message in geometry.py provides useful phase information within the block processing lifecycle. It shows when the most expensive operation (content zone detection) begins. This complements the START/END markers without redundancy.
