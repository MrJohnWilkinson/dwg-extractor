# Chore: Update Docstrings for Mutual Exclusivity Documentation

## Chore Description
Update docstrings in `geometry.py` and `constants.py` to document the mutual exclusivity between Precision Fix and Gap Bridge options. Unit 1 implemented the GUI enforcement of mutual exclusivity (commit `4fca481`), and this unit updates the documentation to reflect that both options solve the same problem (closing small gaps for accurate polygon counts) and cannot be used simultaneously.

The main `_extract_paint_bucket_regions()` docstring was already partially updated in Unit 1, but `_detect_content_zone()` still references outdated "Stage 1/Stage 2" terminology. Additionally, the comment in `constants.py` for `DEFAULT_GAP_BRIDGE_TOLERANCE` needs updating to remove "Stage 2" terminology and document mutual exclusivity.

## Relevant Files
Use these files to resolve the chore:

- **`app/core/geometry.py`** - Contains geometry calculation functions including:
  - `_extract_paint_bucket_regions()` (lines 645-721) - Already partially updated, docstring correctly describes mutual exclusivity
  - `_detect_content_zone()` (lines 990-1187) - Docstring at lines 1006-1009 still references outdated "Stage 1/Stage 2" terminology that needs updating

- **`app/core/constants.py`** - Contains application constants including:
  - `DEFAULT_GAP_BRIDGE_TOLERANCE` comment (lines 217-218) - Still has "Stage 2" terminology that needs updating to document mutual exclusivity with Precision Fix

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Update `_detect_content_zone()` docstring in geometry.py

**File:** `app/core/geometry.py`

**Location:** Lines 1006-1009 in the docstring

**Current text:**
```python
    Two-stage coordinate snapping is applied during region detection:
    - Stage 1 (Precision): Automatically fixes floating-point artifacts
    - Stage 2 (Gap Bridge): Optionally bridges intentional gaps when enabled
```

**Replace with:**
```python
    Coordinate snapping options (mutually exclusive - GUI enforces one or the other):
    - Precision Fix: Snaps coordinates to grid to fix floating-point artifacts
      and small coordinate discrepancies. Uses smaller tolerances.
    - Gap Bridge: Snaps edges to reference geometry to bridge intentional gaps.
      Uses larger tolerances suitable for visible coordinate discrepancies.
    Both options solve the same problem: closing small gaps for accurate polygon counts.
```

### Step 2: Update comment for `DEFAULT_GAP_BRIDGE_TOLERANCE` in constants.py

**File:** `app/core/constants.py`

**Location:** Lines 217-218

**Current text:**
```python
# Stage 2: Default gap bridge tolerances for intentional gap bridging
# These represent typical small gaps in CAD drawings that users may want to bridge
```

**Replace with:**
```python
# Default gap bridge tolerances for closing small gaps in polygon edges.
# Gap Bridge is an alternative to Precision Fix - both close gaps for accurate
# polygon counts. Gap Bridge uses larger tolerances suitable for visible
# coordinate discrepancies in CAD drawings. Mutually exclusive with Precision Fix.
```

### Step 3: Run validation commands to ensure no regressions

Execute the test suite and type checking to verify the docstring changes don't break anything.

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `uv run pytest app/tests/ -q` - Run all tests to ensure no regressions from docstring changes
- `uv run mypy app/` - Run type checking to ensure no type errors introduced

## Notes
- The `_extract_paint_bucket_regions()` docstring was already updated in Unit 1 (commit `4fca481`) to correctly describe mutual exclusivity between Precision Fix and Gap Bridge
- This chore focuses on updating the remaining outdated "Stage 1/Stage 2" terminology in `_detect_content_zone()` and the constants file comment
- These are documentation-only changes with no functional impact, but validation ensures the syntax remains correct
